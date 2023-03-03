import simplejson as json
import hashlib
import pathlib
import textwrap
import logging
import argparse
from datetime import datetime
from decimal import Decimal
from pathvalidate import sanitize_filename
from importlib_metadata import metadata


METADATA = metadata("dyn2py")
HEADER_SEPARATOR = "*" * 60


class DynamoFileException(Exception):
    pass


class PythonNodeNotFoundException(Exception):
    pass


class PythonFileException(Exception):
    pass


class File():
    """Base class for managing files"""

    def __init__(self, filepath: pathlib.Path) -> None:

        self.filepath = filepath
        # basename: only the name of the file, without extension
        self.basename = filepath.stem
        # dirpath: containing folder
        self.dirpath = filepath.parent
        self.realpath = filepath.resolve()
        self.mtime = False
        self.mtimeiso = False
        self.exists = self.filepath.exists()
        self.extension = self.filepath.suffix

        if self.exists:
            logging.debug(f"File exists: {self.filepath}")
            self.mtime = self.filepath.stat().st_mtime
            self.mtimeiso = datetime.fromtimestamp(self.mtime).isoformat()

    def is_newer(self, other_file: "File") -> bool:
        """Check if this file is newer than the other file

        Args:
            other_file (File): The other file

        Returns:
            bool: True if this file is newer or the other doesn't exist
        """
        if self.mtime and other_file.mtime:
            return bool(self.mtime > other_file.mtime)
        elif self.mtime:
            return True
        else:
            return False

    def is_dynamo_file(self) -> bool:
        """Check if this is a Dynamo file

        Returns:
            bool: True if it's Dynamo file
        """
        return bool(self.extension in [".dyn", ".dyf"])

    def is_python_file(self) -> bool:
        """Check if this is a python file

        Returns:
            bool: True if it's python file
        """
        return bool(self.extension == ".py")

    def write(self, args: argparse.Namespace) -> None:
        """Prepare writing file to the disk:
            create backup, process dry-run, call filetype specific write_file() methods

        Args:
            args (argparse.Namespace): parsed arguments
        """
        # Create backup:
        if not args.dry_run and self.filepath.exists() and args.backup:
            backup_filename = sanitize_filename(
                f"{self.basename}_{self.mtimeiso}{self.extension}")
            backup_path = self.dirpath.joinpath(backup_filename)
            logging.info(f"Creating backup to {backup_path}")
            self.filepath.rename(backup_path)

        # Call filetype specific methods:
        if args.dry_run:
            logging.info(
                f"Should write file, but it's a dry-run: {self.filepath}")
        else:
            logging.info(f"Writing file: {self.filepath}")
            self.write_file()

    def write_file(self):
        """Should be implemented in subclasses"""
        pass


class DynamoFile(File):

    def extract_python(self, args: argparse.Namespace) -> None:
        """Extract and write python files

        Args:
            args (argparse.Namespace): parsed arguments
        """

        logging.info(f"Extracting from file: {self.filepath}")

        try:
            self.read()

            # Go through nodes in the file:
            for python_node in self.get_python_nodes():
                if args.python_folder:
                    python_file_path = args.python_folder.joinpath(
                        python_node.filename)
                else:
                    python_file_path = python_node.filepath

                python_file = PythonFile(python_file_path)
                python_file.generate_text(
                    dynamo_file=self, python_node=python_node)

                if python_file.is_newer(self) and not args.force:
                    logging.info(
                        f"Python file is newer, skipping: {python_file.filepath}")
                    continue

                python_file.write(args)

        except DynamoFileException as e:
            logging.warn(e)
            return
        except json.JSONDecodeError:
            logging.error(
                "File is not correctly formatted. Is it a Dynamo2 file?")
            return

    def read(self) -> None:
        """Read Dynamo graph to parameters"""
        logging.debug(f"Reading file: {self.filepath}")

        with open(self.filepath, "r", encoding="utf-8") as input_json:
            self.full_dict = json.load(input_json,
                                       use_decimal=True)
            self.uuid = self.full_dict["Uuid"]
            self.name = self.full_dict["Name"]

    def get_python_nodes(self) -> list["PythonNode"]:
        """Get python nodes from the Dynamo graph

        Returns:
            list[PythonNode]: A list of PythonNodes in the file
        """
        full_python_nodes = [n for n in self.full_dict["Nodes"]
                             if n["NodeType"] == "PythonScriptNode"]

        python_nodes = []

        for p_node in full_python_nodes:
            # The name of the node is stored here:
            node_views = self.full_dict["View"]["NodeViews"]
            python_node = PythonNode(
                node_dict_from_dyn=p_node,
                full_nodeviews_dict_from_dyn=node_views,
                source_dynamo_file=self)
            python_nodes.append(python_node)

        if not python_nodes:
            raise DynamoFileException("No python nodes in this file!")

        return python_nodes

    def get_python_node_by_id(self, node_id: str) -> "PythonNode":
        """Get a PythonNode object from this Dynamo graph, by its id

        Args:
            node_id (str): The id of the python node as string

        Returns:
            PythonNode: The PythonNode with the given id
        """
        python_node_dict = next((
            n for n in self.full_dict["Nodes"] if n["Id"] == node_id
        ), {})
        if not python_node_dict:
            raise PythonNodeNotFoundException(
                f"Node not found with id {node_id}")

        python_node = PythonNode(
            node_dict_from_dyn=python_node_dict)

        return python_node

    def update_python_node(self, python_node: "PythonNode") -> None:
        """Update the code of a PythonNode in this file

        Args:
            python_node (PythonNode): The new node data
        """
        node_dict = next((
            n for n in self.full_dict["Nodes"] if n["Id"] == python_node.id
        ), {})
        if not node_dict:
            raise PythonNodeNotFoundException()
        else:
            node_dict["Code"] = python_node.code

    def write_file(self) -> None:
        """Write this file to the disk. Should be called only from File.write()"""
        with open(self.filepath, "w", encoding="utf-8") as output_file:
            json.dump(self.full_dict, output_file, indent=2,  use_decimal=True)


class PythonFile(File):

    def generate_text(self, dynamo_file: DynamoFile, python_node: "PythonNode") -> None:
        """Generate full text to write with header

        Args:
            dynamo_file (DynamoFile): The source dynamo file
            python_node (PythonNode): The python node to write
        """

        header_notice = """\
                This file was generated with dyn2py from a Dynamo graph.
                Do not edit this section, if you want to update the Dynamo graph!\
                """

        self.header_data = {
            "dyn2py_version": METADATA["Version"],
            "dyn2py_extracted": datetime.now().isoformat(),
            "dyn_uuid": dynamo_file.uuid,
            "dyn_name": dynamo_file.name,
            "dyn_path": dynamo_file.realpath,
            "dyn_modified": dynamo_file.mtimeiso,
            "py_id": python_node.id,
            "py_engine": python_node.engine
        }

        header_string = "\r\n".join(
            [f"{k}:{self.header_data[k]}" for k in self.header_data])
        header_wrapper = '"""'

        self.text = "\r\n".join([
            header_wrapper,
            HEADER_SEPARATOR,
            textwrap.dedent(header_notice),
            HEADER_SEPARATOR,
            header_string,
            HEADER_SEPARATOR,
            header_wrapper,
            python_node.code
        ])

    def update_dynamo(self, args: argparse.Namespace) -> None:
        """Update a the source Dynamo graph from this python script

        Args:
            args (argparse.Namespace): parsed arguments
        """
        self.read()

        dynamo_file_storage = DynamoFileStorage()

        # Update mode, check if needed:
        if args.update:
            if not dynamo_file_storage.is_uuid_on_update_list(self.header_data["dyn_uuid"]):
                logging.info(
                    "Dynamo graph of this script shouldn't be updated")
                return

        # Check if it was already opened:
        logging.debug(f"Open files: {dynamo_file_storage.open_files}")
        dynamo_file = dynamo_file_storage.get_open_file_by_uuid(
            self.header_data["dyn_uuid"])

        # Open and read if it's the first time:
        if not dynamo_file:
            dynamo_file = DynamoFile(
                pathlib.Path(self.header_data["dyn_path"]))

            if not dynamo_file.exists:
                raise FileNotFoundError(
                    f"Dynamo graph not found: {dynamo_file.filepath}")

            dynamo_file.read()

            # Check if uuid is ok:
            if not dynamo_file.uuid == self.header_data["dyn_uuid"]:
                raise DynamoFileException(f"Dynamo graph uuid changed!")

        new_python_node = PythonNode(
            node_id=self.header_data["py_id"],
            engine=self.header_data["py_engine"],
            code=self.code,
            checksum=hashlib.md5(self.code.encode()).hexdigest()
        )

        old_python_node = dynamo_file.get_python_node_by_id(
            self.header_data["py_id"])

        # Check checksum:
        if new_python_node.checksum == old_python_node.checksum:
            logging.info("Python file not changed, skipping")
            return

        if dynamo_file.is_newer(self) and not args.force:
            logging.info("Dynamo graph is newer, skipping")
            return

        logging.info(f"Dynamo graph will be updated: {dynamo_file.filepath}")
        dynamo_file.update_python_node(new_python_node)
        dynamo_file_storage.append_open_file(dynamo_file)

    def read(self) -> None:
        """Read python script to parameters"""
        logging.info(f"Reading file: {self.filepath}")
        with open(self.filepath, mode="r", newline="\r\n", encoding="utf-8") as input_py:
            python_lines = input_py.readlines()

        self.header_data = {}
        header_separator_count = 0
        code_start_line = 0

        for i, line in enumerate(python_lines):
            line = line.strip()
            logging.debug(f"Reading line: {line}")

            # Skip the first lines:
            if header_separator_count < 2:
                if line == HEADER_SEPARATOR:
                    header_separator_count += 1
                continue
            # It's the last line of the header:
            elif line == HEADER_SEPARATOR:
                code_start_line = i+2
                break

            else:
                # Find the location of the separator
                sl = line.find(":")
                if sl == -1:
                    raise PythonFileException("Error reading header!")
                self.header_data[line[0:sl]] = line[sl+1:]

        self.code = "".join(python_lines[code_start_line:])

        logging.debug(f"Header data from python file: {self.header_data}")
        # logging.debug(f"Code from python file: {self.code}")

    def write_file(self) -> None:
        """Write this file to the disk. Should be called only from File.write()"""
        with open(self.filepath, "w", encoding="utf-8") as output_file:
            output_file.write(self.text)


class PythonNode():
    """A Python node with all data"""

    def __init__(self, node_dict_from_dyn: dict = {}, full_nodeviews_dict_from_dyn: dict = {},
                 node_id: str = "", engine: str = "IronPython2", code: str = "", checksum: str = "", name: str = "",
                 source_dynamo_file: DynamoFile = None) -> None:  # type: ignore
        """A PythonNode object

        Args:
            node_dict_from_dyn (dict, optional): The dict of the node from a dyn file. 
                                                 If this is given, string parameters are ignored. Defaults to {}.
            full_nodeviews_dict_from_dyn (dict, optional): The full nodeviews dict from a dyn file. Defaults to {}.
            node_id (str, optional): Id of the node. Defaults to "".
            engine (str, optional): Engine of the node. Defaults to "".
            code (str, optional): The code text. Defaults to "".
            checksum (str, optional): Checksum of the code . Defaults to "".
            name (str, optional): The name of the node. Defaults to "".
            source_dynamo_file (DynamoFile, optional): The file the node is from, to generate filename and filepath. Defaults to None.
        """
        if node_dict_from_dyn:
            self.id = node_dict_from_dyn["Id"]
            # Older dynamo files doesn't have "Engine" property, fall back to the default
            if "Engine" in node_dict_from_dyn:
                self.engine = node_dict_from_dyn["Engine"]
            else:
                self.engine = engine
            self.code = node_dict_from_dyn["Code"]
            self.checksum = hashlib.md5(self.code.encode()).hexdigest()
            if full_nodeviews_dict_from_dyn:
                self.name = next(
                    (v["Name"] for v in full_nodeviews_dict_from_dyn if v["Id"] == node_dict_from_dyn["Id"]), None)
            else:
                self.name = name
        else:
            self.id = node_id
            self.engine = engine
            self.code = code
            self.checksum = checksum
            self.name = name

        # Generate filename and filepath if source is given:
        if source_dynamo_file:
            filename_parts = [source_dynamo_file.basename, self.id]

            # Only add the name of the node if it's changed:
            if self.name and self.name != "Python Script":
                filename_parts.append(self.name)

            logging.debug(f"Generating filename from: {filename_parts}")
            self.filename = sanitize_filename(
                "_".join(filename_parts) + ".py")
            self.filepath = source_dynamo_file.dirpath.joinpath(self.filename)


class DynamoFileStorage():
    open_files: list[DynamoFile] = []
    update_files: list[DynamoFile] = []

    # This is a singleton:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(DynamoFileStorage, cls).__new__(cls)
        return cls.instance

    def get_open_file_by_uuid(self, uuid: str) -> DynamoFile:
        """Get an open Dynamo graph by its uuid

        Args:
            uuid (str): Uuid of the file

        Returns:
            DynamoFile: The file. None if not found
        """
        f = next((d for d in self.open_files if d.uuid == uuid), None)
        if f:
            logging.debug(f"Found open file {f.uuid}")
        return f  # type: ignore

    def is_uuid_on_update_list(self, uuid: str) -> bool:
        """Check if this file is on the list of files to update

        Args:
            uuid (str): Uuid of the file

        Returns:
            bool: True, if the file is on the list
        """
        f = next((d for d in self.update_files if d.uuid == uuid), False)
        return bool(f)

    def append_open_file(self, dynamo_file: DynamoFile) -> None:
        """Add a file to the list of open files

        Args:
            dynamo_file (DynamoFile): The file to add
        """
        if not dynamo_file in self.open_files:
            self.open_files.append(dynamo_file)
            logging.debug("Dynamo file added to open files")

    def write_open_files(self, args: argparse.Namespace) -> None:
        """Save open files to disk

        Args:
            args (argparse.Namespace): parsed arguments
        """
        for f in self.open_files:
            f.write(args)
