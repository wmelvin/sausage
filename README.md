# sausage #

## something about usage ##

**sausage.py** is a command-line tool that does some stuff as described in the help/usage message below.


## help/usage ##

```
usage: sausage.py [-h] [--indent N_SPACES] [--compare-cmd DIFF_CMD]
                  [--usage-only]
                  doc_file [run_cmds ...]

Command-line utility to capture the help/usage message from a program that has
a command-line interface. The help text is then inserted into a copy of a
Markdown document (perhaps a README.md file). More than one program may be
specified if the document includes sections for each.

positional arguments:
  doc_file              Name of the Markdown document file in which to insert
                        the help message text. The document must already have
                        a fenced code block (section marked by lines with
                        triple-backticks before and after), with 'usage:
                        (program_name)' in the block, for each program from
                        which usage text is to be inserted. A modified copy of
                        the document is produced. The original document is not
                        affected.
  run_cmds              One or more commands to launch programs from which to
                        capture the help/usage message. Each must be a single
                        executable command with no arguments. Each must
                        support the -h (help) command-line argument.

optional arguments:
  -h, --help            show this help message and exit
  --indent N_SPACES     Indent the inserted help/usage text by this many
                        spaces.
  --compare-cmd DIFF_CMD
                        Command to launch a file comparison tool. The tool
                        must take the names of two files to compare as the
                        first two command-line arguments. This command will be
                        run to compare the original document to the new
                        modified version.
  --usage-only          Exclude any lines in the help message before the text
                        'usage:' appears (not case-sensitive).
```

## Reference ##

GitHub - Markdown - [Fenced Code Blocks](https://docs.github.com/en/github/writing-on-github/working-with-advanced-formatting/creating-and-highlighting-code-blocks#fenced-code-blocks)


Python Standard Library - [argparse](https://docs.python.org/3/library/argparse.html)
