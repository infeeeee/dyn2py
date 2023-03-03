#!/usr/bin/env python3

import argparse
import pathlib
from importlib_metadata import metadata
import textwrap
import logging
from dyn2py.classes import *


def run():

    METADATA = metadata("dyn2py")

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
                        choices=["CRITICAL",
                                 "ERROR",
                                 "WARNING",
                                 "INFO",
                                 "DEBUG"],
                        default="INFO",
                        help="set log level, possible options: CRITICAL, ERROR, WARNING, INFO, DEBUG ")

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
                        choices=["py", "dyn"],
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

    args = parser.parse_args()

    # Set up logging:
    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=args.loglevel)

    logging.debug(args)

    logging.debug(f"Parsed arguments: {vars(args)}")

    source_files = []

    for source in args.source:

        if not source.exists():
            raise FileNotFoundError(f"Source file does not exist!")

        # Get files from folder:
        elif source.is_dir():
            logging.debug(f"Source is a folder")

            for f in source.iterdir():
                source_files.append(f)

        # It's a single file:
        else:
            source_files.append(source)

    # Dynamo files come first:
    files = [File(f) for f in source_files]
    files.sort(key=lambda f: f.extension)

    # Filters:
    if args.filter == "py":
        files = [f for f in files if f.is_python_file()]
    elif args.filter == "dyn":
        files = [f for f in files if f.is_dynamo_file()]

    # Update mode:
    elif args.update:
        dynamo_files = [DynamoFile(f.filepath)
                        for f in files if f.is_dynamo_file()]
        for d in dynamo_files:
            try:
                logging.info(f"Reading file for update: {d.filepath}")
                d.read()
                DynamoFileStorage().update_files.append(d)
            except json.JSONDecodeError:
                logging.error(
                    "File is not correctly formatted. Is it a Dynamo2 file?")

        # Find python files' folders and remove duplicates:
        if args.python_folder:
            python_folders = [args.python_folder]
        else:
            python_folders = []
            [python_folders.append(f.dirpath)
             for f in dynamo_files if f.dirpath not in python_folders]

        # Add python files:
        source_files = []
        [source_files.extend(pf.iterdir()) for pf in python_folders]
        files = [PythonFile(fp)
                 for fp in source_files if File(fp).is_python_file()]

    # Cycle through files:
    for f in files:

        if f.is_dynamo_file():
            logging.debug("Source is a Dynamo file")
            dynamo_file = DynamoFile(f.filepath)
            dynamo_file.extract_python(args)

        elif f.is_python_file():
            logging.debug("Source is a Python file")
            python_file = PythonFile(f.filepath)
            python_file.update_dynamo(args)

    DynamoFileStorage().write_open_files(args)
