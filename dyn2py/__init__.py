#!/usr/bin/env python3
"""
.. include:: ../README.md
"""
from __future__ import annotations
import argparse
import pathlib
from importlib_metadata import metadata
import textwrap
import logging
import inspect
import sys
from dyn2py.files import *
from dyn2py.options import *


METADATA = metadata("dyn2py")
__version__ = METADATA["Version"]
__all__ = [
    "run",
    "Options",
    "File",
    "DynamoFile",
    "PythonFile",
    "PythonNode",
    "DynamoFileException",
    "PythonNodeNotFoundException",
    "PythonNodeException",
    "PythonFileException"
]


def __dir__():
    return __all__


def __command_line() -> None:
    """Private method for running as a console script"""

    parser = argparse.ArgumentParser(
        prog=METADATA["Name"],
        description=METADATA["Summary"],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            The script by default overwrites older files with newer files.
            Do not move the source Dynamo graphs, or update won't work with them later.
            Multiple sources are supported, separate them by spaces.
            """)
    )

    parser.add_argument("-v", "--version",
                        action="version",
                        version=f'{METADATA["Name"]} {METADATA["Version"]}'
                        )

    parser.add_argument("-l", "--loglevel",
                        metavar="LOGLEVEL",
                        choices=LOGLEVELS,
                        default=DEFAULT_LOGLEVEL,
                        help=f"set log level, possible options: {', '.join(LOGLEVELS)} ")

    parser.add_argument("-n", "--dry-run",
                        help="do not modify files, only show log",
                        action="store_true"
                        )

    parser.add_argument("-F", "--force",
                        help="overwrite even if the files are older",
                        action="store_true")

    parser.add_argument("-b", "--backup",
                        help="create a backup for updated files",
                        action="store_true")

    parser.add_argument("-f", "--filter",
                        choices=FILTERS,
                        help="only check python or Dynamo graphs, skip the others, useful for folders"
                        )

    dynamo_options = parser.add_argument_group(
        title="dynamo options, only for processing Dynamo graphs")

    dynamo_options.add_argument("-u", "--update",
                                help="update Dynamo graph from python scripts in the same folder",
                                action="store_true")

    dynamo_options.add_argument("-p", "--python-folder",
                                metavar="path/to/folder",
                                help="extract python scripts to this folder, read python scripts from here with --update",
                                type=pathlib.Path)

    parser.add_argument("source",
                        type=pathlib.Path,
                        help="path to a Dynamo graph, a python script or a folder containing them",
                        nargs="+"
                        )

    options = parser.parse_args(namespace=Options())

    run(options)


def run(options: Options) -> None:
    """Run an extraction as from the command line

    Args:
        options (Options): Options as from the command line.

    Raises:
        TypeError: options is not an Options object
        FileNotFoundError: If the source file does not exist
    """

    if not isinstance(options, Options):
        raise TypeError("Options have to be a dyn2py.Options() object!")

    from_command_line = bool(inspect.stack()[1].function == "__command_line")

    # Set up logging:
    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=options.loglevel)
    logging.debug(f"Run options: {vars(options)}")

    # Set up sources:
    source_files = []
    for source in options.source:

        if not source.exists():
            if from_command_line:
                # log only if it was called from command line:
                logging.error(f"File does not exist: {source}")
                sys.exit(1)
            else:
                raise FileNotFoundError(f"Source file does not exist!")

        # Get files from folder:
        elif source.is_dir():
            logging.debug(f"Source is a folder")

            for f in source.iterdir():
                source_files.append(f)

        # It's a single file:
        else:
            source_files.append(source)

    # Create file objects
    files = []
    for f in source_files:
        try:
            files.append(File(f))
        except DynamoFileException as e:
            # It's a dynamo1 file
            logging.warning(e)
            continue
        except PythonNodeNotFoundException as e:
            # No python node in this file
            logging.warning(e)
            continue

    # Dynamo files come first, sort sources:
    files.sort(key=lambda f: f.extension)

    # Filters:
    if options.filter == "py":
        files = [f for f in files if f.is_python_file()]
    elif options.filter == "dyn":
        files = [f for f in files if f.is_dynamo_file()]

    # Update mode:
    elif options.update:
        dynamo_files = [DynamoFile(f.filepath)
                        for f in files if f.is_dynamo_file()]
        python_files = set()

        for dynamo_file in dynamo_files:
            p = dynamo_file.get_related_python_files(options)
            if p:
                python_files.update(p)

        files = list(python_files)

    if not files and from_command_line:
        logging.error("No files to process! See previous warnings!")
        sys.exit(1)

    # Cycle through files:
    for f in files:

        if f.is_dynamo_file():
            logging.debug("Source is a Dynamo file")
            f.extract_python(options)

        elif f.is_python_file():
            logging.debug("Source is a Python file")
            f.update_dynamo(options)

    # Write files at the end:
    for f in DynamoFile.open_files | PythonFile.open_files:
        f.write(options)
