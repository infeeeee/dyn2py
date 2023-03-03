# dyn2py

Extract python nodes from Dynamo graphs

## Installation

*TODO*

<!-- ### pip

1. Install python
2. `py -m pip install dyn2py`

### github releases

-->

## Usage

```shell
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

## Development

### Installation

Requirements: git, pip

```shell
git clone https://github.com/infeeeee/dyn2py
cd dyn2py
py -m pip install -e .
```

With venv:

```shell
git clone https://github.com/infeeeee/dyn2py
cd dyn2py
py -m venv .venv
. ./.venv/bin/activate
py -m pip install -e .
```

Build:

```shell
pip install -e .[build]
pyinstaller dyn2py.spec
```