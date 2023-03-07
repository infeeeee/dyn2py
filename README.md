# dyn2py

Extract python nodes from Dynamo graphs

Use cases:

- Track changes in python nodes in source control systems like git
- Work on python code in your favorite code editor outside Dynamo. `dyn2py` can also update Dynamo graphs from the previously exported python files.

## Installation

*TODO*

<!-- ### pip

1. Install python
2. `py -m pip install dyn2py`

### github releases

-->

## Usage

### As a standalone command line program

```
> dyn2py --help
usage: dyn2py [-h] [-l LOGLEVEL] [-n] [-F] [-b] [-f {py,dyn}] [-u] [-p path/to/folder] source

Extract python code from Dynamo graphs

positional arguments:
  source                path to a Dynamo graph, a python script or a folder containing them

options:
  -h, --help            show this help message and exit
  -l LOGLEVEL, --loglevel LOGLEVEL
                        set log level, possible options: CRITICAL, ERROR, WARNING, INFO, DEBUG
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
```

### As a python module

Full API documentation available here: https://infeeeee.github.io/dyn2py

Most basic example to extract all nodes next to a dynamo file:

```python
import dyn2py

dynamo_file = dyn2py.DynamoFile("path/to/dynamofile.dyn")
dynamo_file.extract_python()
```

Change options like with the command line switches with the `Options` class:

```python
import dyn2py

# Create a backup on overwrite, read python files from a different folder:
options = dyn2py.Options(
    backup=True,
    python_folder="path/to/pythonfiles")

dynamo_file = dyn2py.DynamoFile("path/to/dynamofile")
python_files = dynamo_file.get_related_python_files(options)

# Read python files and update the graph:
if python_files:
    for python_file in python_files:
        python_file.update_dynamo(options)

# Don't forget to save at the end:
dynamo_file.write(options)
```

## Development

### Installation

Requirements: git, pip

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

### Build

```
pip install -e .[build]
pyinstaller dyn2py.spec
```

### Generate module documentation

```
pip install -e .[doc]
pdoc -d google -o docs dyn2py
```
