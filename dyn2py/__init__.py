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
    "PythonFileException"
]


def run(options: Options | None = None) -> None:
    """Run an extraction as from the command line

    Args:
        options (Options): Options as from the command line.

    Raises:
        FileNotFoundError: If the source file does not exist
    """

    if not options:

        parser = argparse.ArgumentParser(
            prog=METADATA["Name"],
            description=METADATA["Summary"],
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=textwrap.dedent("""\
            The script by default overwrites older files with newer files.
            Do not move the source Dynamo graphs, or update won't work with them later.
            """)
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
                            action="append"
                            )

        options = parser.parse_args(namespace=Options())

    # Set up logging:
    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=options.loglevel)
    logging.debug(options)
    logging.debug(f"Parsed arguments: {vars(options)}")

    # Set up sources:
    files = []
    for source in options.source:

        if not source.exists():
            raise FileNotFoundError(f"Source file does not exist!")

        # Get files from folder:
        elif source.is_dir():
            logging.debug(f"Source is a folder")

            for f in source.iterdir():
                files.append(File(f))

        # It's a single file:
        else:
            files.append(File(source))

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

    # Cycle through files:
    for f in files:

        if f.is_dynamo_file():
            logging.debug("Source is a Dynamo file")

            try:
                f.extract_python(options)
            except DynamoFileException as e:
                logging.error(f"{e} Skipping")

        elif f.is_python_file():
            logging.debug("Source is a Python file")
            f.update_dynamo(options)

    # Dynamo files are written only at the end, so they don't get updated too frequently
    for f in DynamoFile.open_files:
        f.write(options)
