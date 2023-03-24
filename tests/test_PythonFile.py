import unittest
import dyn2py
import shutil
from time import sleep
import os

from tests.support import *


class TestPythonFile(unittest.TestCase):

    def test_init(self):
        extract_single_node_dyn()

        py1 = dyn2py.PythonFile(f"{OUTPUT_DIR}/single_node_1c5d99792882409e97e132b3e9f814b0.py")

        dyn2py.DynamoFile.open_files.clear()
        dyn = dyn2py.DynamoFile(f"{INPUT_DIR}/single_node.dyn")
        node = list(dyn.python_nodes)[0]
        py2 = dyn2py.PythonFile(filepath=node.filepath,
                                dynamo_file=dyn, python_node=node)

        for py in [py1, py2]:

            self.assertEqual(len(py.code), 17)
            self.assertEqual(len(py.text.split(os.linesep)), 32, msg=py.filepath)
            self.assertIs(type(py.header_data), dict)
            self.assertTrue(py in dyn2py.PythonFile.open_files)

    def test_update_dynamo(self):
        extract_single_node_dyn(modify_py=True)

        dyn2py.DynamoFile.open_files.clear()
        dyn2py.PythonFile.open_files.clear()

        py1 = dyn2py.PythonFile(
            f"{OUTPUT_DIR}/single_node_1c5d99792882409e97e132b3e9f814b0.py")

        dyn1 = dyn2py.DynamoFile(f"{INPUT_DIR}/single_node.dyn")

        # This shouldn't modify, as this file was not updated:
        py1.update_dynamo()
        self.assertFalse(dyn1.modified)

        # The modified files should update:
        py2 = dyn2py.PythonFile(f"{OUTPUT_DIR}/single_node_mod.py")
        py2.update_dynamo()
        self.assertTrue(dyn1.modified)

        dyn2py.DynamoFile.open_files.clear()

        # Make sure that the dyn file is newer:
        sleep(1)
        shutil.copy(f"{INPUT_DIR}/single_node.dyn",
                    f"{OUTPUT_DIR}/single_node.dyn")
        dyn2 = dyn2py.DynamoFile(f"{OUTPUT_DIR}/single_node.dyn")
        py2.header_data["dyn_path"] = f"{OUTPUT_DIR}/single_node.dyn"
        self.assertFalse(py2.is_newer(dyn2))

        # This shouldn't modify, as it is newer:
        py2.update_dynamo()
        self.assertFalse(dyn2.modified)

        # It should work with force:
        opt = dyn2py.Options(force=True)
        py2.update_dynamo(options=opt)
        self.assertTrue(dyn2.modified)

    def test_get_source_dynamo_file(self):
        extract_single_node_dyn()
        dyn2py.DynamoFile.open_files.clear()
        dyn2py.PythonFile.open_files.clear()

        py1 = dyn2py.PythonFile(
            f"{OUTPUT_DIR}/single_node_1c5d99792882409e97e132b3e9f814b0.py")

        dyn1 = py1.get_source_dynamo_file()
        self.assertEqual(len(dyn2py.DynamoFile.open_files), 1)
        self.assertIn(dyn1, dyn2py.DynamoFile.open_files)

        dyn2 = py1.get_source_dynamo_file()
        self.assertIs(dyn1, dyn2)

        dyn2py.DynamoFile.open_files.clear()

        with self.assertRaises(dyn2py.DynamoFileException):
            py1.header_data["dyn_uuid"] = "wrong-uuid"
            py1.get_source_dynamo_file()

    def test_write(self):
        extract_single_node_dyn()
        dyn2py.DynamoFile.open_files.clear()
        dyn2py.PythonFile.open_files.clear()

        py1 = dyn2py.PythonFile(
            f"{OUTPUT_DIR}/single_node_1c5d99792882409e97e132b3e9f814b0.py")

        dyn1 = py1.get_source_dynamo_file()
        node = list(dyn1.python_nodes)[0]
        py2 = dyn2py.PythonFile(
            node.filepath, dynamo_file=dyn1, python_node=node)
        self.assertIsNot(py1, py2)
        self.assertEqual(py1.code, py2.code)
        for d in py1.header_data:
            if not d == "dyn2py_extracted":
                self.assertEqual(py1.header_data[d], py2.header_data[d])
