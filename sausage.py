#!/usr/bin/env python3

from collections import namedtuple
from datetime import datetime
from pathlib import Path

import argparse
import subprocess
import sys


AppOptions = namedtuple("AppOptions", "doc_path, programs")


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
        + "document is produced. The original document is not affected."
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

    args = ap.parse_args()

    doc_path = Path(args.doc_file).expanduser().resolve()
    assert doc_path.exists()

    prog_list = []
    for cmd in args.run_cmds:
        if 0 < len(cmd):
            usage_tag = f"usage: {Path(cmd.split()[0]).stem}"
            prog_list.append((cmd, usage_tag))

    opts = AppOptions(doc_path, prog_list)

    return opts


def get_help_text(run_cmd) -> str:
    print("\nGetting usage (help) message from command.")
    # print(f"Running: {run_cmd}")
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
        # assert result.returncode == 0
        s = result.stdout.strip()
    except Exception as e:
        raise e

    return s


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

    print(f"\nWriting '{out_path}'")
    with open(out_path, "w") as out_file:
        for s in out_lines:
            out_file.write(f"{s}\n")


def main(argv):
    opts = get_opts(argv)

    print(f"\nReading '{opts.doc_path}'")

    with open(opts.doc_path, "r") as f:
        doc_lines = [s.rstrip() for s in f.readlines()]

    for run_cmd, usage_tag in opts.programs:

        ix_before, ix_after = index_usage_section(
            doc_lines, opts.doc_path, usage_tag
        )

        a = doc_lines[: ix_before + 1]
        b = doc_lines[ix_after:]

        help_text = get_help_text(run_cmd)

        indent = " " * 4

        doc_lines = a + [f"{indent}{t}" for t in help_text.split("\n")] + b

    write_output(opts, doc_lines)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
