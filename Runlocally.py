#!/usr/bin/env python3
"""
RunLocally.py -- run one job of a Condor submission locally, in LocalTrials/.

    ./RunLocally.py ConfFiles/test.jdl 3
    ./RunLocally.py ConfFiles/test.jdl 3 --list     # see every ProcId first
    ./RunLocally.py ConfFiles/test.jdl 3 -n         # show what would happen

It reads the submit file the same way condor_submit does, works out what ProcId
N would have been given, then builds that job's sandbox under

    LocalTrials/<jdl name>.proc<N>/

copying in the executable and everything in Transfer_Input_Files -- flattened to
their basenames, which is what the worker node sees and why the arguments in
JobInfo/*.txt say "test_signal.txt" and not "FilePaths/test_signal.txt".  Then
it runs the executable there with that job's arguments, output on your terminal
and saved to job.out next to the sandbox.

Run it from the same directory you run condor_submit from (the repo root), so
that relative paths in the submit file resolve; or pass --submit-dir.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

MACRO = re.compile(r"\$\(([^()]+)\)")

# Submit commands this script cares about. Everything else is kept as a macro
# but otherwise ignored (request_memory, universe, Log, ...).
WANTED = ("executable", "arguments", "transfer_input_files", "initialdir",
          "environment", "output", "error", "batch_name", "request_cpus")


# --------------------------------------------------------------------------- #
# parsing the submit file
# --------------------------------------------------------------------------- #
def read_logical_lines(path):
    """Yield submit-file lines, joining backslash continuations, dropping comments."""
    with open(path) as f:
        buf = ""
        for raw in f:
            line = raw.rstrip("\n")
            stripped = line.strip()
            if not buf and (not stripped or stripped.startswith("#")):
                continue
            if line.rstrip().endswith("\\"):
                buf += line.rstrip()[:-1]
                continue
            yield (buf + line).strip()
            buf = ""
        if buf.strip():
            yield buf.strip()


def parse_jdl(path):
    """
    Return (macros, queue) where macros is a dict keyed by lowercased name and
    queue describes the final queue statement.
    """
    macros, queue = {}, {"kind": "count", "count": 1, "vars": [], "file": None}

    for line in read_logical_lines(path):
        low = line.lower()

        if low.startswith("queue"):
            rest = line[5:].strip()
            if not rest:
                queue = {"kind": "count", "count": 1, "vars": [], "file": None}
            elif re.match(r"^\d+$", rest):
                queue = {"kind": "count", "count": int(rest), "vars": [], "file": None}
            else:
                m = re.match(r"^(.*?)\s+from\s+(.+)$", rest, re.IGNORECASE)
                if m:
                    names = [v.strip() for v in re.split(r"[,\s]+", m.group(1)) if v.strip()]
                    queue = {"kind": "from", "count": None,
                             "vars": names or ["item"],
                             "file": m.group(2).strip().strip('"')}
                else:
                    m = re.match(r"^(.*?)\s+in\s+\((.*)\)$", rest, re.IGNORECASE | re.DOTALL)
                    if m:
                        names = [v.strip() for v in re.split(r"[,\s]+", m.group(1)) if v.strip()]
                        items = [i.strip() for i in re.split(r"[,\n]", m.group(2)) if i.strip()]
                        queue = {"kind": "in", "count": len(items), "vars": names or ["item"],
                                 "file": None, "items": items}
                    else:
                        die(f"cannot read this queue statement: {line!r}")
            continue

        if "=" in line:
            name, _, value = line.partition("=")
            name = name.strip().lower()
            # '+AccountingGroup = ...' and 'MY.Foo = ...' are ClassAd attributes
            if name.startswith(("+", "my.")):
                continue
            macros[name] = value.strip()

    return macros, queue


def expand(text, macros, undefined=None):
    """Expand $(name) the way condor_submit does; unknown names become empty."""
    if text is None:
        return ""
    for _ in range(25):
        hit = MACRO.search(text)
        if not hit:
            break
        def sub(m):
            key = m.group(1).strip().lower()
            if key in macros:
                return macros[key]
            if undefined is not None and key not in undefined:
                undefined.append(m.group(1).strip())
            return ""
        text = MACRO.sub(sub, text)
    return text.strip()


def queue_items(queue, submit_dir):
    """The list of per-job values: one entry per ProcId."""
    if queue["kind"] == "from":
        path = os.path.join(submit_dir, queue["file"])
        if not os.path.isfile(path):
            die(f"queue file not found: {path}")
        with open(path) as f:
            return [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]
    if queue["kind"] == "in":
        return queue["items"]
    return [""] * queue["count"]


def bind_item(item, names, macros):
    """Assign one queue-file line to the queue variable(s)."""
    if len(names) == 1:
        macros[names[0].lower()] = item
        return
    parts = [p.strip() for p in (item.split(",") if "," in item else item.split())]
    for i, n in enumerate(names):
        if i == len(names) - 1:
            macros[n.lower()] = " ".join(parts[i:]) if i < len(parts) else ""
        else:
            macros[n.lower()] = parts[i] if i < len(parts) else ""


def die(msg):
    sys.stderr.write(f"RunLocally: {msg}\n")
    sys.exit(2)


# --------------------------------------------------------------------------- #
# building the sandbox
# --------------------------------------------------------------------------- #
def bring_in(src, dest_dir, how, notes):
    """Put src into dest_dir under its basename, as Condor's file transfer would."""
    name = os.path.basename(src.rstrip("/"))
    dest = os.path.join(dest_dir, name)
    if not os.path.exists(src):
        notes.append(f"MISSING: {src}")
        return None
    if os.path.lexists(dest):
        return dest
    if how == "link":
        os.symlink(os.path.abspath(src), dest)
    elif os.path.isdir(src):
        shutil.copytree(src, dest, symlinks=True)
    else:
        shutil.copy2(src, dest)
    return dest


def transfer_entries(value):
    return [e.strip() for e in value.split(",") if e.strip()]


def parse_environment(value):
    """environment = "A=1 B='two words'"  ->  dict"""
    import shlex
    env, value = {}, value.strip()
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1].replace("''", "'")
    try:
        toks = shlex.split(value)
    except ValueError:
        toks = value.split()
    for t in toks:
        if "=" in t:
            k, _, v = t.partition("=")
            env[k] = v
    return env


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description="Run a single job from a Condor submit file locally, "
                    "in a sandbox under LocalTrials/.")
    ap.add_argument("jdl", help="path to the condor submit file, e.g. ConfFiles/test.jdl")
    ap.add_argument("procid", nargs="?", type=int,
                    help="which job of the cluster to run (0 = first line of the queue file)")
    ap.add_argument("-l", "--list", action="store_true",
                    help="list every ProcId and its arguments, then stop")
    ap.add_argument("-n", "--dry-run", action="store_true",
                    help="set the sandbox up and print the command, run nothing")
    ap.add_argument("-d", "--dir", default="LocalTrials", metavar="DIR",
                    help="where sandboxes go (default LocalTrials)")
    ap.add_argument("--submit-dir", default=".", metavar="DIR",
                    help="directory relative paths in the submit file resolve against "
                         "(default: current directory, i.e. where you'd run condor_submit)")
    ap.add_argument("--link", action="store_true",
                    help="symlink the input files instead of copying them")
    ap.add_argument("--keep", action="store_true",
                    help="reuse the sandbox if it already exists instead of wiping it")
    ap.add_argument("--cluster", default="local", metavar="ID",
                    help="value for $(Cluster) (default: local)")
    ap.add_argument("--arg", action="append", default=[], metavar="EXTRA",
                    help="extra argument appended to the job's arguments (repeatable)")
    opts = ap.parse_args()

    submit_dir = os.path.abspath(opts.submit_dir)
    jdl = opts.jdl if os.path.isabs(opts.jdl) else os.path.join(submit_dir, opts.jdl)
    if not os.path.isfile(jdl):
        die(f"submit file not found: {jdl}")

    macros, queue = parse_jdl(jdl)
    items = queue_items(queue, submit_dir)

    if opts.list:
        print(f"{len(items)} job(s) in {opts.jdl}"
              + (f"  (queue {' '.join(queue['vars'])} from {queue['file']})"
                 if queue["kind"] == "from" else ""))
        for i, it in enumerate(items):
            print(f"  {i:>5}  {it}")
        return 0

    if opts.procid is None:
        die("give a ProcId, or use --list to see them")
    if not 0 <= opts.procid < len(items):
        die(f"ProcId {opts.procid} is out of range: this cluster has "
            f"{len(items)} job(s), 0..{len(items) - 1}")

    # macros Condor defines for us
    macros.setdefault("cluster", str(opts.cluster))
    macros["clusterid"] = macros["cluster"]
    macros["procid"] = str(opts.procid)
    macros["process"] = str(opts.procid)
    macros["step"] = "0"
    if queue["kind"] != "count":
        bind_item(items[opts.procid], queue["vars"], macros)
        macros.setdefault("item", items[opts.procid])

    undefined = []
    exe_rel = expand(macros.get("executable"), macros, undefined)
    if not exe_rel:
        die("no Executable in the submit file")
    arguments = expand(macros.get("arguments"), macros, undefined)
    if opts.arg:
        arguments = (arguments + " " + " ".join(opts.arg)).strip()
    inputs = transfer_entries(expand(macros.get("transfer_input_files", ""), macros, undefined))

    iwd = submit_dir
    if macros.get("initialdir"):
        initial = expand(macros["initialdir"], macros, undefined)
        iwd = initial if os.path.isabs(initial) else os.path.join(submit_dir, initial)

    def resolve(p):
        return p if os.path.isabs(p) else os.path.normpath(os.path.join(iwd, p))

    tag = f"{os.path.splitext(os.path.basename(jdl))[0]}.proc{opts.procid}"
    sandbox = os.path.abspath(os.path.join(opts.dir, tag))
    if os.path.isdir(sandbox) and not opts.keep:
        shutil.rmtree(sandbox)
    os.makedirs(sandbox, exist_ok=True)

    how = "link" if opts.link else "copy"
    notes = []
    for entry in inputs:
        if "://" in entry:
            notes.append(f"NOT fetched (remote): {entry}  -- xrdcp it into the sandbox "
                         f"yourself if the job needs it up front")
            continue
        src = resolve(entry)
        if entry.endswith("/") and os.path.isdir(src):      # 'dir/' transfers the contents
            for child in sorted(os.listdir(src)):
                bring_in(os.path.join(src, child), sandbox, how, notes)
        else:
            bring_in(src, sandbox, how, notes)

    exe_src = resolve(exe_rel)
    exe = bring_in(exe_src, sandbox, how, notes)
    if exe is None:
        die(f"executable not found: {exe_src}")
    os.chmod(exe, os.stat(exe).st_mode | 0o100)

    argv = [exe] + __import__("shlex").split(arguments)
    env = dict(os.environ)
    if macros.get("environment"):
        env.update(parse_environment(expand(macros["environment"], macros, undefined)))
    env["_CONDOR_SCRATCH_DIR"] = sandbox
    env["_CONDOR_JOB_IWD"] = iwd
    env["CONDOR_LOCAL_TRIAL"] = tag

    print(f"submit file   {jdl}")
    print(f"ProcId        {opts.procid} of {len(items)}")
    if queue["kind"] == "from":
        print(f"queue line    {items[opts.procid]}")
    print(f"executable    {exe_src}")
    print(f"arguments     {arguments}")
    print(f"sandbox       {sandbox}")
    print(f"files in      {', '.join(sorted(os.listdir(sandbox))) or '(none)'}")
    for n in notes:
        print(f"  ! {n}")
    if undefined:
        print(f"  ! undefined macro(s), expanded to nothing: {', '.join(sorted(set(undefined)))}")
    print()

    if opts.dry_run:
        import shlex
        print("would run, with cwd = sandbox:")
        print("  " + " ".join(shlex.quote(a) for a in argv))
        return 0

    # The log lives beside the sandbox, not inside it, so the job sees exactly
    # the files Condor would have transferred and nothing else.
    logpath = sandbox + ".out"
    print(f"--- running (output also going to {logpath}) " + "-" * 20)
    with open(logpath, "w") as log:
        proc = subprocess.Popen(argv, cwd=sandbox, env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1)
        for line in proc.stdout:
            sys.stdout.write(line)
            log.write(line)
        rc = proc.wait()
    print("-" * 60)
    print(f"exit code {rc}   sandbox: {sandbox}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
