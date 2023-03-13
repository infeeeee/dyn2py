from __future__ import annotations
import simplejson as json
import hashlib
import pathlib
import textwrap
import logging
from datetime import datetime
from decimal import Decimal
from pathvalidate import sanitize_filename
from importlib_metadata import metadata

from dyn2py.exceptions import *
from dyn2py.options import Options


METADATA = metadata("dyn2py")
HEADER_SEPARATOR = "*" * 60


class File():
    """Base class for managing files"""

    def __init__(self, filepath: pathlib.Path | str, read_from_disk: bool = True) -> None:
        """Generate a file object. If the path is correct it will become a DynamoFile or PythonFile object

        Args:
            filepath (pathlib.Path | str): Path to the python file or Dynamo graph
            read_from_disk (bool, optional): Read the file from disk. Set to false to get only metadata. Defaults to True.
        """

        self.filepath: pathlib.Path
        """Path to the file as a pathlib.Path object"""
        if isinstance(filepath, str):
            self.filepath = pathlib.Path(filepath)
        else:
            self.filepath = filepath

        self.basename: str = self.filepath.stem
        """Only the name of the file, without path or extension"""
        self.dirpath: pathlib.Path = self.filepath.parent
        """Containing folder"""
        self.realpath: pathlib.Path = self.filepath.resolve()
        """Full resolved path to the file"""
        self.mtime: float = 0.0
        """Modification time. 0 if does not exist"""
        self.mtimeiso: str = ""
        """Modification time as an iso formatted string"""

        self.exists: bool = self.filepath.exists()
        """If the file exists"""
        self.extension: str = self.filepath.suffix
        """File extension as string"""
        self.modified: bool = False
        """If an existing file was modified"""

        # Change class if extension is correct:
        if self.is_dynamo_file():
            self.__class__ = DynamoFile

            # Read DynamoFiles, they should exist:
            if read_from_disk:
                self.read_file()

        elif self.is_python_file():
            self.__class__ = PythonFile

            # Python files can be virtual:
            if self.exists and read_from_disk:
                self.read_file()

        if self.exists and read_from_disk:
            logging.debug(f"File exists: {self.filepath}")
            self.mtime = self.filepath.stat().st_mtime
            self.mtimeiso = datetime.fromtimestamp(self.mtime).isoformat()

    def read_file(self):
        """Should be implemented in subclasses"""
        pass

    def is_newer(self, other_file: "File") -> bool:
        """Check if this file is newer than the other file

        Args:
            other_file(File): The other file

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

    def write(self, options: Options | None = None) -> None:
        """Prepare writing file to the disk:
            create backup, process dry-run, call filetype specific write_file() methods
            Should be called on subclasses!

        Args:
            options(Options | None, optional): Run options. Defaults to None.

        Raises:
            TypeError: If called on a File object
        """

        if not options:
            options = Options()

        # This should only work on subclasses:
        if type(self).__name__ == "File":
            raise TypeError("This method shouldn't be called on File objects!")

        if not self.modified:
            logging.debug("File not modified, not saving")
            return

        # Create backup:
        if not options.dry_run and self.filepath.exists() and options.backup:
            backup_filename = sanitize_filename(
                f"{self.basename}_{self.mtimeiso}{self.extension}")
            backup_path = self.dirpath.joinpath(backup_filename)
            logging.info(f"Creating backup to {backup_path}")
            self.filepath.rename(backup_path)

        # Call filetype specific methods:
        if options.dry_run:
            logging.info(
                f"Should write file, but it's a dry-run: {self.filepath}")
        else:
            logging.info(f"Writing file: {self.filepath}")
            self.write_file()

    def write_file(self):
        """Should be implemented in subclasses"""
        pass


class DynamoFile(File):
    """A Dynamo file, subclass of File()"""

    full_dict: dict
    """The contents of the Dynamo file, as dict."""
    uuid: str
    """The uuid of the graph."""
    name: str
    """The name of the graph, read from the file, not the filename"""
    python_nodes: set[PythonNode]
    """Python node objects, read from this file."""

    open_files: set[DynamoFile] = set()
    """A set of open Dynamo files, before saving. Self added by read()"""

    def extract_python(self, options: Options | None = None) -> None:
        """Extract and write python files

        Args:
            options(Options | None, optional): Run options. Defaults to None.
        """

        if not options:
            options = Options()

        logging.info(f"Extracting from file: {self.filepath}")

        # Go through nodes in the file:
        for python_node in self.python_nodes:
            if options.python_folder:
                python_file_path = options.python_folder.joinpath(
                    python_node.filename)
            else:
                python_file_path = python_node.filepath

            python_file = PythonFile(
                filepath=python_file_path,
                dynamo_file=self,
                python_node=python_node
            )

            if python_file.is_newer(self) and not options.force:
                logging.info(
                    f"Existing file is newer, skipping: {python_file.filepath}")
                continue

            python_file.write(options)

    def read_file(self, reread: bool = False) -> None:
        """Read Dynamo graph to parameters. Automatically called by __init__()

        Args:
            reread (bool, optional): Reread the file, even if it was read already. Defaults to False.

        Raises:
            FileNotFoundError: The file does not exist
            DynamoFileException: If the file is a Dynamo 1 file
            json.JSONDecodeError: If there are any other problem with the file
            PythonNodeNotFoundException: No python nodes in the file
        """

        if not self.exists:
            raise FileNotFoundError

        if not self in self.open_files or reread:

            logging.debug(f"Reading file: {self.filepath}")
            # Read the json:
            try:
                with open(self.filepath, "r", encoding="utf-8") as input_json:
                    self.full_dict = json.load(input_json,
                                               use_decimal=True)

            except json.JSONDecodeError as e:
                with open(self.filepath, "r", encoding="utf-8") as input_json:
                    if input_json.readline().startswith("<Workspace Version="):
                        raise DynamoFileException("This is a Dynamo 1 file!")
                    else:
                        raise e

            # Parameters:
            self.uuid = self.full_dict["Uuid"]
            self.name = self.full_dict["Name"]
            self.open_files.add(self)

            full_python_nodes = [n for n in self.full_dict["Nodes"]
                                 if n["NodeType"] == "PythonScriptNode"]
            # The name of the node is stored here:
            node_views = self.full_dict["View"]["NodeViews"]

            if not full_python_nodes:
                raise PythonNodeNotFoundException(
                    "No python nodes in this file!")

            self.python_nodes = set()

            # Create PythonNodes from the dict:
            for p_node in full_python_nodes:
                python_node = PythonNode(
                    node_dict_from_dyn=p_node,
                    dynamo_file=self)
                self.python_nodes.add(python_node)

    def get_python_node_by_id(self, node_id: str) -> "PythonNode":
        """Get a PythonNode object from this Dynamo graph, by its id

        Args:
            node_id(str): The id of the python node as string

        Returns:
            PythonNode: The PythonNode with the given id

        Raises:
            PythonNodeNotFoundException: No python node with this id
        """

        python_node = next((
            p for p in self.python_nodes if p.id == node_id
        ), None)

        if not python_node:
            raise PythonNodeNotFoundException(
                f"Node not found with id {node_id}")

        return python_node

    def update_python_node(self, python_node: PythonNode) -> None:
        """Update the code of a PythonNode in this file

        Args:
            python_node(PythonNode): The new node

        Raises:
            PythonNodeNotFoundException: Existing node not found
        """

        # Find the old node:
        python_node_in_file = self.get_python_node_by_id(python_node.id)

        node_dict = next((
            n for n in self.full_dict["Nodes"] if n["Id"] == python_node.id
        ), {})

        if not node_dict or not python_node_in_file:
            raise PythonNodeNotFoundException()

        # Remove the old and add the new:
        self.python_nodes.remove(python_node_in_file)
        self.python_nodes.add(python_node)

        # Update the dict:
        node_dict["Code"] = python_node.code

        self.modified = True

    def write_file(self) -> None:
        """Write this file to the disk. Should be called only from File.write()"""
        with open(self.filepath, "w", encoding="utf-8", newline="") as output_file:
            json.dump(self.full_dict, output_file, indent=2,  use_decimal=True)

    def get_related_python_files(self, options: Options | None = None) -> list["PythonFile"]:
        """Get python files exported from this Dynamo file

        Args:
            options(Options | None, optional): Run options. Defaults to None.

        Returns:
            list[PythonFile]: A list of PythonFile objects
        """
        if not options:
            options = Options()

        # Find the folder of the python files
        if options.python_folder:
            python_folder = options.python_folder
        else:
            python_folder = self.dirpath

        python_files_in_folder = [PythonFile(f) for f in python_folder.iterdir()
                                  if File(f, read_from_disk=False).is_python_file()]

        related_python_files = [
            p for p in python_files_in_folder if p.get_source_dynamo_file().uuid == self.uuid]

        return related_python_files

    @staticmethod
    def get_open_file_by_uuid(uuid: str) -> "DynamoFile | None":
        """Get an open Dynamo graph by its uuid

        Args:
            uuid(str): Uuid of the file
        Returns:
            DynamoFile: The file. None if not found
        """
        f = next((d for d in DynamoFile.open_files if d.uuid == uuid), None)
        if f:
            logging.debug(f"Found open file {f.uuid}")
        return f


class PythonFile(File):
    """A Python file, subclass of File()"""

    code: str
    """The python code as a string."""
    header_data: dict
    """Parsed dict from the header of a python file."""
    text: str
    """Full contents of the file before writing."""

    open_files: set["PythonFile"] = set()
    """A set of open Python files."""

    def __init__(self,
                 filepath: pathlib.Path | str,
                 dynamo_file: DynamoFile | None = None,
                 python_node: PythonNode | None = None
                 ) -> None:
        """Generate a PythonFile. If both dynamo_file and python_node given, generate the text of the file, do not read from disk

        Args:
            filepath (pathlib.Path | str): Path to the python file
            dynamo_file (DynamoFile | None, optional): The source dynamo file. Defaults to None.
            python_node (PythonNode | None, optional): The python node to write. Defaults to None.
        """

        # Generate the text, if dynamo file and python node were given:
        if python_node and dynamo_file:
            # Do not read from disk:
            super().__init__(filepath, read_from_disk=False)

            header_notice = """\
            This file was generated with dyn2py from a Dynamo graph.
            Do not edit this section, if you want to update the Dynamo graph!\
            """

            # Double escape path:
            dyn_path_string = str(dynamo_file.realpath)
            if "\\" in dyn_path_string:
                dyn_path_string = dyn_path_string.replace("\\", "\\\\")

            self.header_data = {
                "dyn2py_version": METADATA["Version"],
                "dyn2py_extracted": datetime.now().isoformat(),
                "dyn_uuid": dynamo_file.uuid,
                "dyn_name": dynamo_file.name,
                "dyn_path": dyn_path_string,
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

            self.modified = True

        else:
            # Try to read from disk:
            super().__init__(filepath, read_from_disk=True)

        self.open_files.add(self)

    def read_file(self, reread: bool = False) -> None:
        """Read python script to parameters

        Args:
            reread (bool, optional): Reread the file, even if it was read already. Defaults to False.

        Raises:
            FileNotFoundError: The file does not exist
            PythonFileException: Some error reading the file
        """
        if not self.exists:
            raise FileNotFoundError

        # Only read if it's not already open:
        if not self in self.open_files or reread:

            logging.info(f"Reading file: {self.filepath}")
            with open(self.filepath, mode="r", newline="", encoding="utf-8") as input_py:
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
            self.open_files.add(self)

            logging.debug(f"Header data from python file: {self.header_data}")
            # logging.debug(f"Code from python file: {self.code}")

    def update_dynamo(self, options: Options | None = None) -> None:
        """Update a the source Dynamo graph from this python script

        Args:
            options (Options | None, optional): Run options. Defaults to None.
        """

        if not options:
            options = Options()

        # Check if it was already opened:
        dynamo_file = DynamoFile.get_open_file_by_uuid(
            self.header_data["dyn_uuid"])

        # Open if it's the first time:
        if not dynamo_file:
            dynamo_file = self.get_source_dynamo_file()

        new_python_node = PythonNode(python_file=self)

        old_python_node = dynamo_file.get_python_node_by_id(
            self.header_data["py_id"])

        # Check checksum:
        if new_python_node.checksum == old_python_node.checksum:
            logging.info("Python file not changed, skipping")
            return

        if dynamo_file.is_newer(self) and not options.force:
            logging.info("Dynamo graph is newer, skipping")
            return

        logging.info(f"Dynamo graph will be updated: {dynamo_file.filepath}")
        dynamo_file.update_python_node(new_python_node)

    def get_source_dynamo_file(self) -> DynamoFile:
        """Get the source Dynamo file of this PythonFile

        Raises:
            FileNotFoundError: The dynamo file not found
            DynamoFileException: The uuid of the dynamo file changed

        Returns:
            DynamoFile: The DynamoFile
        """
        dynamo_file = DynamoFile(
            pathlib.Path(self.header_data["dyn_path"]))

        if not dynamo_file.exists:
            raise FileNotFoundError(
                f"Dynamo graph not found: {dynamo_file.filepath}")

        # Check if uuid is ok:
        if not dynamo_file.uuid == self.header_data["dyn_uuid"]:
            raise DynamoFileException(f"Dynamo graph uuid changed!")

        return dynamo_file

    def write_file(self) -> None:
        """Write this file to the disk. Should be called only from File.write()"""
        with open(self.filepath, "w", encoding="utf-8", newline="") as output_file:
            output_file.write(self.text)


class PythonNode():
    """A Python node with all data"""

    id: str
    """The id of the node"""
    engine: str
    """The engine of the node, IronPython2 or CPython3"""
    code: str
    """The full code"""
    checksum: str
    """The checksum of the code, for checking changes"""
    name: str
    """The name of the node"""
    filename: pathlib.Path | str
    """The filename the node should be saved as, including the .py extension"""
    filepath: pathlib.Path
    """The path is shoul"""

    def __init__(self,
                 node_dict_from_dyn: dict = {},
                 dynamo_file: DynamoFile | None = None,
                 python_file: PythonFile | None = None,
                 ) -> None:
        """A PythonNode object. Add dict and dynamo_file, or only python_file.

        Args:
            node_dict_from_dyn (dict, optional): The dict of the node from a dyn file. Defaults to {}.
            dynamo_file (DynamoFile, optional): The file the node is from. Defaults to None.
            python_file (PythonFile, optional): The python file to be converted to node. Defaults to None.

        Raises:
            PythonNodeException: Wrong arguments were given
        """
        # Initialize from dynamo file:
        if node_dict_from_dyn and dynamo_file and not python_file:
            self.id = node_dict_from_dyn["Id"]

            # Older dynamo files doesn't have "Engine" property, fall back to IronPython2
            if "Engine" in node_dict_from_dyn:
                self.engine = node_dict_from_dyn["Engine"]
            else:
                self.engine = "IronPython2"

            self.code = node_dict_from_dyn["Code"]

            # Get the name of the node:
            self.name = next(
                (v["Name"] for v in dynamo_file.full_dict["View"]["NodeViews"]
                 if v["Id"] == node_dict_from_dyn["Id"]), "")

            # Generate the filename:
            filename_parts = [dynamo_file.basename, self.id]

            # Only add the name of the node if it's changed:
            if self.name and self.name != "Python Script":
                filename_parts.append(self.name)

            logging.debug(f"Generating filename from: {filename_parts}")
            self.filename = sanitize_filename(
                "_".join(filename_parts) + ".py")
            self.filepath = dynamo_file.dirpath.joinpath(self.filename)

        elif python_file and not node_dict_from_dyn and not dynamo_file:
            self.id = python_file.header_data["py_id"]
            self.engine = python_file.header_data["py_engine"]
            self.code = python_file.code
            self.filename = python_file.basename + ".py"
            self.filepath = python_file.filepath

        else:
            raise PythonNodeException

        # Calculate checksum:
        self.checksum = hashlib.md5(self.code.encode()).hexdigest()
