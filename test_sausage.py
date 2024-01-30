from __future__ import annotations

import shutil
from pathlib import Path
from stat import S_IXUSR  # https://docs.python.org/3/library/stat.html#stat.S_IXUSR
from textwrap import dedent

import pytest

import sausage


def test_main_wo_args():
    with pytest.raises(SystemExit) as e:
        sausage.main([])
    #  Should raise SystemExit(2).
    assert str(e.value) == "2"


def test_get_opts():
    args = ["doc_name.md", "cmd1", "cmd2"]
    opts = sausage.get_opts(args)
    assert str(opts.doc_path.name) == "doc_name.md"
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
    ],
)
def get_usage_params(request):
    return request.param[0], request.param[1]


def test_index_usage_section_2(get_usage_params):
    cmd_arg, doc_line = get_usage_params
    args = ["doc_name.md", cmd_arg]
    opts = sausage.get_opts(args)
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


def test_get_help_lines(monkeypatch):
    def mock_get_help_text(run_cmd, opts):
        return dedent(
            """
            someapp version 1.2.3"

            usage: someapp [-h]

            someapp does something.
            """
        )

    monkeypatch.setattr(sausage, "get_help_text", mock_get_help_text)

    lines = sausage.get_help_lines(
        "someapp",
        sausage.AppOptions(
            doc_path=None,
            programs=None,
            indent_level=0,
            diff_tool=None,
            usage_only=False,
            python_path=None,
            run_as_module=False,
        ),
    )

    assert len(lines) == 7
    assert "someapp" in "\n".join(lines)

    lines = sausage.get_help_lines(
        "someapp",
        sausage.AppOptions(
            doc_path=None,
            programs=None,
            indent_level=0,
            diff_tool=None,
            usage_only=True,  # <- changed
            python_path=None,
            run_as_module=False,
        ),
    )
    assert len(lines) == 4
    assert "version" not in "\n".join(lines)


@pytest.fixture
def make_test_py_file(tmp_path: Path) -> tuple[Path, Path]:
    """
    Create README.md and testme.py in a temporary location.
    Return two Path objects in a tuple (doc_file, py_file).
    """
    doc_file = tmp_path / "README.md"
    doc_text = dedent(
        """
        # TEST ME

        ```
        usage: testme
        ```
        """
    )
    doc_file.write_text(doc_text)

    py_file = tmp_path / "testme.py"

    py_code = "#!/usr/bin/env python3"
    # Putting the shebang in the dedent text block puts it on the second line
    # and it needs to be on the first.
    py_code += dedent(
        """
        import argparse

        ap = argparse.ArgumentParser(description="This is a test")
        ap.add_argument("some_file", action="store", help="Name of some file")
        args = ap.parse_args(None)
        print(args)
        """
    )
    py_file.write_text(py_code)

    return (doc_file, py_file)


@pytest.fixture
def make_test_py_module(tmp_path: Path) -> tuple[Path, Path]:
    """
    Create README.md and a testme module in a temporary location.
    The testme module has __init__.py, __main__.py, and app.py.
    Return two Path objects in a tuple (doc_file, py_mod).
    """
    doc_file = tmp_path / "README.md"
    doc_file.write_text(
        dedent(
            """
            # TEST ME

            ```
            usage: testme
            ```
            """
        )
    )

    py_mod = tmp_path / "testme"
    py_mod.mkdir()

    py_init = py_mod / "__init__.py"
    py_init.touch()

    py_main = py_mod / "__main__.py"
    py_main.write_text(
        dedent(
            """
            import app

            app.main()
            """
        )
    )

    py_file = py_mod / "app.py"
    py_file.write_text(
        dedent(
            """
            import argparse

            ap = argparse.ArgumentParser(description="This is a test")
            ap.add_argument("some_file", action="store", help="Name of some file")
            args = ap.parse_args(None)
            print(args)
            """
        )
    )

    return (doc_file, py_mod)


def test_on_python_file_with_pypath(make_test_py_file):
    doc_file, py_file = make_test_py_file

    py_exe = shutil.which("python3")
    if not py_exe:
        py_exe = shutil.which("python")

    args = [str(doc_file), str(py_file), "--python-path", py_exe]
    result = sausage.main(args)
    assert result == 0

    files = list(doc_file.parent.glob("README_MODIFIED*.md"))
    assert len(files) == 1

    out_file = files[0]
    assert "usage: testme.py [-h] some_file" in out_file.read_text()


def test_on_python_file_no_pypath(make_test_py_file):
    doc_file, py_file = make_test_py_file

    # Make executable by owner.
    py_file.chmod(py_file.stat().st_mode | S_IXUSR)

    args = [str(doc_file), str(py_file)]
    result = sausage.main(args)
    assert result == 0

    files = list(doc_file.parent.glob("README_MODIFIED*.md"))
    assert len(files) == 1

    out_file = files[0]
    assert "usage: testme.py [-h] some_file" in out_file.read_text()


def test_on_python_module_with_pypath(make_test_py_module):
    doc_file, py_mod = make_test_py_module

    py_exe = shutil.which("python3")
    if not py_exe:
        py_exe = shutil.which("python")

    args = [str(doc_file), str(py_mod), "--python-path", py_exe, "--module"]
    result = sausage.main(args)
    assert result == 0

    files = list(doc_file.parent.glob("README_MODIFIED*.md"))
    assert len(files) == 1

    out_file = files[0]
    assert "usage: testme [-h] some_file" in out_file.read_text()


def test_on_python_module_no_pypath(make_test_py_module):
    doc_file, py_mod = make_test_py_module

    args = [str(doc_file), str(py_mod), "--module"]
    result = sausage.main(args)
    assert result == 0

    files = list(doc_file.parent.glob("README_MODIFIED*.md"))
    assert len(files) == 1

    out_file = files[0]
    assert "usage: testme [-h] some_file" in out_file.read_text()
