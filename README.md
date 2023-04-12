[![GitHub release (latest by date)](https://img.shields.io/github/v/release/infeeeee/dyn2py?style=flat-square)](https://github.com/infeeeee/dyn2py/releases/latest)
[![PyPI](https://img.shields.io/pypi/v/dyn2py?style=flat-square)](https://pypi.org/project/dyn2py/)
[![GitHub Release Date](https://img.shields.io/github/release-date/infeeeee/dyn2py?style=flat-square)](https://github.com/infeeeee/dyn2py/releases/latest)
[![GitHub last commit (branch)](https://img.shields.io/github/last-commit/infeeeee/dyn2py/main?style=flat-square)](https://github.com/infeeeee/dyn2py/commits/main)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/infeeeee/dyn2py/unittests.yml?label=tests&style=flat-square)](https://github.com/infeeeee/dyn2py/actions/workflows/unittests.yml)
[![GitHub](https://img.shields.io/github/license/infeeeee/dyn2py?style=flat-square)](https://github.com/infeeeee/dyn2py/blob/main/LICENSE)

# dyn2py

Extract python code from Dynamo graphs

Use cases:

- Track changes in python nodes in source control systems like git
- Work on python code in your favorite code editor outside Dynamo. `dyn2py` can also update Dynamo graphs from previously exported python files.

## Installation

### Windows portable and installer

Prebuilt portable exe and installer available from github releases.

No requirements, just download `dyn2py.exe` or `dyn2py-installer.exe` from release assets:

https://github.com/infeeeee/dyn2py/releases/latest

Installer automatically adds the install folder to the path, so simply `dyn2py` can be called from anywhere.

### With pip

For usage as a module or as a command line program

Requirements: python, pip

```
pip install dyn2py
```

## Usage

### As a standalone command line program

```
> dyn2py --help
usage: dyn2py [-h] [-v] [-l LOGLEVEL] [-n] [-F] [-b] [-f {py,dyn}] [-u] [-p path/to/folder] [source ...]

Extract python code from Dynamo graphs

positional arguments:
  source                path to a Dynamo graph, a python script or a folder containing them

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -l LOGLEVEL, --loglevel LOGLEVEL
                        set log level, possible options: HEADLESS, CRITICAL, ERROR, WARNING, INFO, DEBUG
  -n, --dry-run         do not modify files, only show log
  -F, --force           overwrite even if the files are older
  -b, --backup          create a backup for updated files
  -f {py,dyn}, --filter {py,dyn}
                        only check python or Dynamo graphs, skip the others, useful for folders

dynamo options, only for processing Dynamo graphs:
  -u, --update          update Dynamo graph from python scripts in the same folder
  -p path/to/folder, --python-folder path/to/folder
                        extract python scripts to this folder, read python scripts from here with --update

The script by default overwrites older files with newer files.
Do not move the source Dynamo graphs, or update won't work with them later.
Multiple sources are supported, separate them by spaces.
HEADLESS loglevel only prints modified filenames.
```

#### Examples

*Notes: In Windows cmd use backward slashes as path separators, in any other shells use forward slashes. Powershell accepts both of them. Wrap paths with spaces in double quotes.*

```shell
# Extract all nodes next to a Dynamo file:
dyn2py path/to/dynamofile.dyn

# Update a Dynamo file from previously exported and modified python files:
dyn2py --update path/to/dynamofile.dyn

# Extract python nodes to a specific folder, process multiple Dynamo files:
dyn2py --python-folder path/to/pythonfiles path/to/dynamofile1.dyn path/to/dynamofile2.dyn

# Update Dynamo files from python files from a folder. Only check python files, create backups:
dyn2py --filter py --backup path/to/pythonfiles
```

#### Git hooks

Git Hooks are a built-in feature of Git that allow developers to automate tasks throughout the Git workflow. Read more here: https://githooks.com/

With the `pre-commit` hook it's possible to add more files to the currently initialized commit.

You can find an example pre-commit hook here: [pre-commit](pre-commit). Copy this file to the `.git/hooks` folder of your repo of Dynamo graph. This folder is hidden by default, but it should exist in all initialized git repo. Do not rename this file.

This script will go through staged `.dyn` files and export python scripts from them, and add them to the current commit. Now you can check check changed lines in a diff tool!

### As a python module

Full API documentation available here: https://infeeeee.github.io/dyn2py

Most basic example to extract all nodes next to a Dynamo file:

```python
import dyn2py

dynamo_file = dyn2py.DynamoFile("path/to/dynamofile.dyn")
dynamo_file.extract_python()
dyn2py.PythonFile.write_open_files()
```

Change options like with the command line switches with the `Options` class:

```python
import dyn2py

# Create a backup on overwrite, read python files from a different folder:
options = dyn2py.Options(
    backup=True,
    python_folder="path/to/pythonfiles")

dynamo_file = dyn2py.DynamoFile("path/to/dynamofile.dyn")
python_files = dynamo_file.get_related_python_files(options)

# Read python files and update the graph:
[python_file.update_dynamo(options) for python_file in python_files]

# Don't forget to save at the end:
dynamo_file.write(options)
```

For more examples check tests in the [tests folder on Github](https://github.com/infeeeee/dyn2py/tree/main/tests)

They should work in Dynamo, inside CPython3 nodes.

## Troubleshooting

If you have a problem, open an [issue on Github](https://github.com/infeeeee/dyn2py/issues)

You can also ask about this project on [Dynamo Forum](https://forum.dynamobim.com/), don't forget to ping me: [@infeeeee](https://forum.dynamobim.com/u/infeeeee)

## Limitations

Only supports Dynamo 2 files, Dynamo 1 files are reported and ignored. Please update them to Dynamo 2 by opening them in Dynamo 2.

Both IronPython2 and CPython3 nodes are supported! IronPython2 nodes won't be updated to CPython3, they will be imported as-is.

## Development

### Installation

Requirements: git, python, pip

```
git clone https://github.com/infeeeee/dyn2py
cd dyn2py
pip install -e .
```

With venv:

```
git clone https://github.com/infeeeee/dyn2py
cd dyn2py
venv .venv
. ./.venv/bin/activate
pip install -e .
```

### Build for Windows

```
pip install -e .[build]
pyinstaller dyn2py.spec
```

### Create installer for Windows

- Install Inno Setup: https://jrsoftware.org/isdl.php
- Build an exe
- Run `dyn2py-installer.ps1` in powershell

### Live module documentation

```
pip install -e .[doc]
pdoc -d google dyn2py
```

### Unit tests

VSCode should automatically discover unit tests. 

To run them manually:

```
python -m unittest discover -v -s ./tests -p "test_*.py"
```

### New release

1. Update version number in `pyproject.toml`
2. Create a publish a git tag with that number

## License

GPL-3.0

