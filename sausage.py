#!/usr/bin/env python3

from collections import namedtuple
from pathlib import Path

import argparse
import subprocess
import sys


AppOptions = namedtuple("AppOptions", "help_cmd, target_file")


def get_opts(argv) -> AppOptions:

    ap = argparse.ArgumentParser(
        description="Command-line utility to capture usage (help) message and "
        + "insert it into a target file (perhaps a README)."
    )

    ap.add_argument(
        "help_cmd",
        action="store",
        help="Command to run to get help message from an application "
        + "(usually someapp -h).",
    )

    ap.add_argument(
        "target_filename",
        action="store",
        help="Name of the file in which to insert the help message text.",
    )

    args = ap.parse_args()

    opts = AppOptions(args.help_cmd, args.target_filename)

    assert Path(opts.target_file).exists()

    return opts


def get_help_text(opts: AppOptions) -> str:
    cmds = opts.help_cmd.split()
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

    print(f"BEGIN_HELP\n{get_help_text(opts)}\nEND_HELP")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
