#!/usr/bin/env python3

from collections import namedtuple
from datetime import datetime
from pathlib import Path

import argparse
import subprocess
import sys


AppOptions = namedtuple("AppOptions", "run_cmd, doc_path")


def get_opts(argv) -> AppOptions:

    ap = argparse.ArgumentParser(
        description="Command-line utility to capture usage (help) message and "
        + "insert it into a target file (perhaps a README)."
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
        help="Name of the file in which to insert the help message text.",
    )

    args = ap.parse_args()

    p = Path(args.doc_file).expanduser().resolve()
    assert p.exists()

    opts = AppOptions(args.run_cmd, p)

    return opts


def get_help_text(opts: AppOptions) -> str:
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


def main(argv):
    opts = get_opts(argv)

    help_text = get_help_text(opts)

    assert "usage:" in help_text

    # print(f"BEGIN_HELP\n{help_text}\nEND_HELP")

    print(f"Reading '{opts.doc_path}'")

    with open(opts.doc_path, "r") as f:
        doc_lines = f.readlines()

    ds = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name = f"{opts.doc_path.stem}_{ds}{opts.doc_path.suffix}"
    out_path = Path(opts.doc_path).parent.joinpath(out_name)

    assert not out_path.exists()

    print(f"Writing '{out_path}'")

    with open(out_path, "w") as out_file:
        for line in doc_lines:
            out_file.write(f"{line}\n")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
