
import pytest

from pathlib import Path

import sausage


def test_main_wo_args():
    with pytest.raises(SystemExit) as e:
        sausage.main(["sausage.py"])
    #  Should raise SystemExit(2).
    assert str(e.value) == "2"


def test_get_opts():
    argv = ["sausage.py", "doc_name.md", "cmd1", "cmd2"]
    opts = sausage.get_opts(argv)
    assert "doc_name.md" == str(opts.doc_path.name)
    assert ("cmd1", "usage: cmd1") in opts.programs
    assert ("cmd2", "usage: cmd2") in opts.programs
    assert opts.indent_level == 0
    assert opts.diff_tool is None


@pytest.fixture(
    scope="module",
    params=[
        ("cmd1", "usage: cmd1"),
        ("cmd2", "Usage: cmd2"),
        ("Cmd3", "usage: Cmd3"),
        ("Cmd4", "USAGE: Cmd4"),
    ]
)
def get_usage_params(request):
    return request.param[0], request.param[1]


def test_index_usage_section_2(get_usage_params):
    cmd_arg, doc_line = get_usage_params
    argv = ["sausage.py", "doc_name.md", cmd_arg]
    opts = sausage.get_opts(argv)
    lines = [
        "# Testing #",
        "",
        "```",
        doc_line,
        "```",
        "",
    ]
    tag = opts.programs[0][1]
    doc_path = Path("doc_name.md")
    print(f"tag='{tag}'")
    ia, ib = sausage.index_usage_section(lines, doc_path, tag)
    assert ia == 2
    assert ib == 4
