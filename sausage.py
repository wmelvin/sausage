#!/usr/bin/env python3

from collections import namedtuple
from datetime import datetime
from pathlib import Path

import argparse
import subprocess
import sys


AppOptions = namedtuple("AppOptions", "run_cmd, doc_path, usage_tag")


def get_opts(argv) -> AppOptions:

    ap = argparse.ArgumentParser(
        description="Command-line utility to capture usage (help) message and "
        + "insert it into a a copy of a Markdown document (perhaps README.md)."
    )

    ap.add_argument(
        "run_cmd",
        action="store",
        help="Command to run to get help message from an application "
        + "(usually someapp -h).",
    )

    ap.add_argument(
        "doc_file",
        action="store",
        help="Name of the Markdown document file in which to insert the help "
        + "message text.",
    )

    args = ap.parse_args()

    doc_path = Path(args.doc_file).expanduser().resolve()
    assert doc_path.exists()

    usage_tag = f"usage: {Path(args.run_cmd.split()[0]).stem}"

    opts = AppOptions(args.run_cmd, doc_path, usage_tag)

    return opts


def get_help_text(opts: AppOptions) -> str:
    print("\nGetting usage (help) message from command.")
    print(f"Running: {opts.run_cmd}")
    cmds = opts.run_cmd.split()
    try:
        result = subprocess.run(
            cmds,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        assert result.returncode == 0
        s = result.stdout.strip()
    except Exception as e:
        raise e

    return s


def index_usage_section(opts: AppOptions, doc_lines):
    print(f"\nLooking for '{opts.usage_tag}' in '{opts.doc_path.name}',")
    tbt = "```"
    tbt_lines = []

    usage_lines = []

    for ix, line in enumerate(doc_lines):
        s = line.strip()
        if s.startswith(tbt) and not (6 < len(s) and s.endswith(tbt)):
            tbt_lines.append(ix)
        if opts.usage_tag in s.lower():
            usage_lines.append(ix)

    if 0 == len(usage_lines):
        print(f"No reference to '{opts.usage_tag}' found in document.")
        print("Cannot proceed.")
        sys.exit(1)

    #  For this to work, there needs to be only one "usage:" reference
    #  in the document.
    if 1 < len(usage_lines):
        print(
            f"More than one reference to '{opts.usage_tag}' found in document."
        )
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

    ix_before, ix_after = index_usage_section(opts, doc_lines)

    a = doc_lines[: ix_before + 1]
    b = doc_lines[ix_after:]

    help_text = get_help_text(opts)

    indent = " " * 4

    out_lines = a + [f"{indent}{t}" for t in help_text.split("\n")] + b

    write_output(opts, out_lines)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
