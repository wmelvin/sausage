#!/usr/bin/env python3

from collections import namedtuple
from datetime import datetime
from pathlib import Path

import argparse
import subprocess
import sys


AppOptions = namedtuple("AppOptions", "doc_path, programs, indent_level")


def get_opts(argv) -> AppOptions:

    ap = argparse.ArgumentParser(
        description="Command-line utility to capture the help/usage message "
        + "from a program that has a command-line interface. The help text is "
        + "then inserted into a copy of a Markdown document (perhaps "
        + "a README.md file). More than one program may be specified if the "
        + "document includes sections for each."
    )

    ap.add_argument(
        "doc_file",
        action="store",
        help="Name of the Markdown document file in which to insert the help "
        + "message text. The document must already have a fenced code block "
        + "(section marked by lines with triple-backticks before and after), "
        + "with 'usage: (program_name)' in the block, for each program from "
        + "which usage text is to be inserted. A modified copy of the "
        + "document is produced. The original document is not affected.",
    )

    ap.add_argument(
        "run_cmds",
        nargs="*",
        action="store",
        help="One or more commands to launch programs from which to capture "
        + "the help/usage message. Each must be a single executable command "
        + "with no arguments. Each must support the -h (help) command-line "
        + "argument.",
    )

    ap.add_argument(
        "--indent",
        dest="n_spaces",
        type=int,
        default=0,
        action="store",
        help="Indent the inserted help/usage text by this many spaces.",
    )

    args = ap.parse_args()

    doc_path = Path(args.doc_file).expanduser().resolve()
    assert doc_path.exists()

    prog_list = []
    for cmd in args.run_cmds:
        if 0 < len(cmd):
            usage_tag = f"usage: {Path(cmd.split()[0]).stem}"
            prog_list.append((cmd, usage_tag))

    opts = AppOptions(doc_path, prog_list, args.n_spaces)

    return opts


def get_help_text(run_cmd):
    print("\nGetting usage (help) message from command.")
    cmds = run_cmd.split()
    cmds.append("-h")
    print(f"Run process: {cmds}")
    try:
        result = subprocess.run(
            cmds,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        # s = result.stdout.strip()
        s = result.stdout
    except Exception as e:
        # TODO: What exceptions to expect?
        raise e
    return s


def get_help_lines(run_cmd, indent_level):
    text = get_help_text(run_cmd)
    spaces = " " * indent_level
    lines = []
    for line in text.split("\n"):
        if 0 == len(line):
            lines.append(line)
        else:
            lines.append(f"{spaces}{line}")
    return lines


def index_usage_section(doc_lines, doc_path, usage_tag):
    #  For the process to work, there needs to be a single reference to the
    #  usage_tag in the document, and it needs to be in a fenced code block
    #  enclosed by lines with triple-backticks.

    print(f"\nLooking for '{usage_tag}' in '{doc_path.name}',")

    tbt = "```"
    tbt_lines = []
    usage_lines = []

    for ix, line in enumerate(doc_lines):
        s = line.strip()
        if s.startswith(tbt) and not (6 < len(s) and s.endswith(tbt)):
            tbt_lines.append(ix)
        if usage_tag in s.lower():
            usage_lines.append(ix)

    if 0 == len(usage_lines):
        print(f"No reference to '{usage_tag}' found in document.")
        print("Cannot proceed.")
        sys.exit(1)
        # TODO: Print warning and return (None, None) instead of exiting.

    if 1 < len(usage_lines):
        print(f"More than one reference to '{usage_tag}' found in document.")
        print("Cannot proceed.")
        sys.exit(1)

    tbt_before = -1
    tbt_after = -1

    for x in tbt_lines:
        if x <= usage_lines[0]:
            tbt_before = x
        elif tbt_after < 0:
            tbt_after = x

    if tbt_before < 0 or tbt_after < 0:
        print("Could not find surrounding triple-backticks to indicate code")
        print("section for usage text.")
        print("Cannot proceed.")
        sys.exit(1)

    return tbt_before, tbt_after


def write_output(opts: AppOptions, out_lines):
    #  Write to a copy of the source document with a date_time tag added
    #  to the file name. I don't trust this enough yet to directly modify
    #  the document. For now, using a diff tool to check and apply chanegs.

    ds = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name = f"{opts.doc_path.stem}_MODIFIED_{ds}{opts.doc_path.suffix}"
    out_path = Path(opts.doc_path).parent.joinpath(out_name)

    assert not out_path.exists()

    print(f"\nSaving '{out_path}'")
    with open(out_path, "w") as out_file:
        for s in out_lines:
            out_file.write(f"{s}\n")


def main(argv):
    opts = get_opts(argv)

    print(f"\nReading '{opts.doc_path}'")

    with open(opts.doc_path, "r") as f:
        orig_lines = [s.rstrip() for s in f.readlines()]

    doc_lines = orig_lines[:]

    for run_cmd, usage_tag in opts.programs:

        ia, ib = index_usage_section(doc_lines, opts.doc_path, usage_tag)
        # TODO: Check ia and ib for None.

        help_lines = get_help_lines(run_cmd, opts.indent_level)
        a = doc_lines[: ia + 1]
        b = doc_lines[ib:]
        doc_lines = a + help_lines + b

    (Path.cwd() / "debug1.txt").write_text("\n".join(orig_lines))
    (Path.cwd() / "debug2.txt").write_text("\n".join(doc_lines))

    if orig_lines == doc_lines:
        print("\nNo changes to document. Nothing to save.\n")
    else:
        write_output(opts, doc_lines)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
