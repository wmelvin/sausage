#!/usr/bin/env python3

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

app_version = "2024.01.1"

app_title = f"sausage.py - something about usage - version {app_version}"


class AppOptions(NamedTuple):
    doc_path: Path
    programs: list
    indent_level: int
    diff_tool: str
    usage_only: bool


warnings = []


def get_opts(argv) -> AppOptions:
    ap = argparse.ArgumentParser(
        description="Command-line utility to capture the help/usage message "
        "from a program that has a command-line interface. The help text is "
        "then inserted into a copy of a Markdown document (perhaps "
        "a README.md file). More than one program may be specified if the "
        "document includes sections for each."
    )

    ap.add_argument(
        "doc_file",
        action="store",
        help="Name of the Markdown document file in which to insert the help "
        "message text. The document must already have a fenced code block "
        "(section marked by lines with triple-backticks before and after), "
        "with 'usage: (program_name)' in the block, for each program from "
        "which usage text is to be inserted. A modified copy of the "
        "document is produced. The original document is not affected.",
    )

    ap.add_argument(
        "run_cmds",
        nargs="*",
        action="store",
        help="One or more commands to launch programs from which to capture "
        "the help/usage message. Each must be a single executable command "
        "with no arguments. Each must support the -h (help) command-line "
        "argument.",
    )

    ap.add_argument(
        "--indent",
        dest="n_spaces",
        type=int,
        default=0,
        action="store",
        help="Indent the inserted help/usage text by this many spaces.",
    )

    ap.add_argument(
        "--compare-cmd",
        dest="diff_cmd",
        action="store",
        help="Command to launch a file comparison tool. The tool must take "
        "the names of two files to compare as the first two command-line "
        "arguments. This command will be run to compare the original "
        "document to the new modified version.",
    )

    ap.add_argument(
        "--usage-only",
        dest="usage_only",
        action="store_true",
        help="Exclude any lines in the help message before the text 'usage:' "
        "appears (not case-sensitive).",
    )

    args = ap.parse_args(argv[1:])

    doc_path = Path(args.doc_file).expanduser().resolve()

    prog_list = []
    for cmd in args.run_cmds:
        if cmd:
            cmd_path = Path(cmd.split()[0])
            cmd_name = cmd_path.stem

            #  If running __init__.py in a module then substitue the
            #  module name.
            if cmd_name == "__init__":
                cmd_name = cmd_path.parent.name

            usage_tag = f"usage: {cmd_name}"

            prog_list.append((cmd, usage_tag))

    return AppOptions(
        doc_path, prog_list, args.n_spaces, args.diff_cmd, args.usage_only
    )


def run_compare(run_cmd, left_file, right_file):
    print(f"\nCompare\n  L: {left_file}\n  R: {right_file}\n")
    cmds = [run_cmd, left_file, right_file]
    print(f"Run process: {cmds}")
    try:
        result = subprocess.run(
            cmds,  # noqa: S603
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            check=True,
        )
    except Exception as e:
        # TODO: What exceptions to expect/handle?
        raise e
    print(f"Process return code: {result.returncode}")


def get_help_text(run_cmd):
    print("\nGetting usage (help) message from command.")
    cmds = run_cmd.split()
    cmds.append("-h")
    print(f"Run process: {cmds}")
    try:
        result = subprocess.run(
            cmds,  # noqa: S603
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            check=True,
        )
        s = result.stdout.rstrip()
    except Exception as e:
        # TODO: What exceptions to expect/handle?
        raise e

    #  If running __init__.py in a module then substitue the module name.
    cmd_path = Path(run_cmd)
    if cmd_path.name == "__init__.py":
        s = s.replace("__init__.py", cmd_path.parent.name)

    return s


def get_help_lines(run_cmd, indent_level, usage_only):
    text = get_help_text(run_cmd)
    spaces = " " * indent_level
    lines = []
    usage_found = not usage_only
    for line in text.split("\n"):
        if not usage_found:
            usage_found = "usage:" in line.lower()
        if usage_found:
            if line:
                lines.append(f"{spaces}{line}")
            else:
                lines.append(line)
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

        if s.startswith(tbt) and not (len(s) > 6 and s.endswith(tbt)):  # noqa: PLR2004
            tbt_lines.append(ix)

        #  Match on usage_tag is case-insensitive.
        if usage_tag.lower() in s.lower():
            usage_lines.append(ix)

    if not usage_lines:
        warnings.append(f"WARNING: No reference to '{usage_tag}' found in document.")
        warnings.append("Cannot process help/usage for this program.")
        return None, None

    if len(usage_lines) > 1:
        warnings.append(
            f"WARNING: More than one reference to '{usage_tag}' found in document."
        )
        warnings.append("Cannot process help/usage for this program.")
        return None, None

    tbt_before = -1
    tbt_after = -1

    for x in tbt_lines:
        if x <= usage_lines[0]:
            tbt_before = x
        elif tbt_after < 0:
            tbt_after = x

    if tbt_before < 0 or tbt_after < 0:
        warnings.append(
            "Could not find surrounding triple-backticks to indicate fenced "
            f"code block for '{usage_tag}'."
        )
        warnings.append("Cannot process help/usage for this program.")
        return None, None

    return tbt_before, tbt_after


def write_output(opts: AppOptions, out_lines):
    """
    Writes the modified document lines to a new file with "MODIFIED" and
    a date_time tag added to the file name. Returns the file name.
    """

    ds = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name = f"{opts.doc_path.stem}_MODIFIED_{ds}{opts.doc_path.suffix}"
    out_path = Path(opts.doc_path).parent.joinpath(out_name)

    assert not out_path.exists()  # noqa: S101

    print(f"\nSaving '{out_path}'")
    with out_path.open("w") as out_file:
        for s in out_lines:
            out_file.write(f"{s}\n")
    return str(out_path)


def main(argv):
    print(f"\n{app_title}\n")

    opts = get_opts(argv)

    print(f"\nReading '{opts.doc_path}'")

    if not opts.doc_path.exists():
        sys.stderr.write(f"\nERROR: Cannot find '{opts.doc_path}'\n")
        return 1

    with opts.doc_path.open() as f:
        orig_lines = [s.rstrip() for s in f.readlines()]

    doc_lines = orig_lines[:]

    for run_cmd, usage_tag in opts.programs:
        ia, ib = index_usage_section(doc_lines, opts.doc_path, usage_tag)
        if ia is not None:
            help_lines = get_help_lines(run_cmd, opts.indent_level, opts.usage_only)
            a = doc_lines[: ia + 1]
            b = doc_lines[ib:]
            doc_lines = a + help_lines + b

    # (Path.cwd() / "DEBUG-A.txt").write_text("\n".join(orig_lines))
    # (Path.cwd() / "DEBUG-B.txt").write_text("\n".join(doc_lines))

    if orig_lines == doc_lines:
        print("\n*** Existing help/usage text is current. Nothing to do.\n")
    else:
        file_name = write_output(opts, doc_lines)
        if opts.diff_tool is not None:
            run_compare(opts.diff_tool, str(opts.doc_path), file_name)

    if warnings:
        for warning in warnings:
            print(warning)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
