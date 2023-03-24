import unittest
import dyn2py
import pathlib
import shutil
import simplejson as json

from tests.support import *


class TestDynamoFile(unittest.TestCase):

    def test_init(self):
        dyn2py.DynamoFile.open_files.clear()

        dyn = dyn2py.DynamoFile(f"{INPUT_DIR}/python_nodes.dyn")

        self.assertEqual(dyn.uuid, "3c3b4c05-9716-4e93-9360-ca0637cb5486")
        self.assertEqual(dyn.name, "python_nodes")
        self.assertTrue(dyn in dyn2py.DynamoFile.open_files)

        # Dynamo 1 file:
        with self.assertRaises(dyn2py.DynamoFileException):
            dyn1 = dyn2py.DynamoFile(f"{INPUT_DIR}/dynamo1file.dyn")

        # Not existing file:
        with self.assertRaises(FileNotFoundError):
            dyn2 = dyn2py.DynamoFile(f"{INPUT_DIR}/not_existing.dyn")

        # No python nodes:
        with self.assertRaises(dyn2py.PythonNodeNotFoundException):
            dyn2 = dyn2py.DynamoFile(f"{INPUT_DIR}/no_python.dyn")

    def test_get_python_nodes(self):
        dyn = dyn2py.DynamoFile(f"{INPUT_DIR}/python_nodes.dyn")
        py_node = dyn.get_python_node_by_id("d7704617c75e4bf1a5c387b7c3f001ea")

        self.assertEqual(len(dyn.python_nodes), 6)
        self.assertTrue(py_node)
        self.assertIn(py_node, dyn.python_nodes)
        self.assertEqual(py_node.checksum, "e830a6ae6b395bcfd4e5a40da48f3bfc")

        with self.assertRaises(dyn2py.PythonNodeNotFoundException):
            dyn.get_python_node_by_id("wrongid")

    def test_extract_python(self):
        cleanup_output_dir()
        dyn2py.PythonFile.open_files.clear()

        opt = dyn2py.Options(python_folder=OUTPUT_DIR)
        dyn = dyn2py.DynamoFile(f"{INPUT_DIR}/python_nodes.dyn")
        dyn.extract_python(options=opt)

        self.assertEqual(len(dyn2py.PythonFile.open_files), 6)

        for f in dyn2py.PythonFile.open_files:
            f.write()

        output_dir = pathlib.Path(OUTPUT_DIR)
        self.assertEqual(len(list(output_dir.iterdir())), 6)

    def test_get_open_file_by_uuid(self):
        dyn2py.DynamoFile.open_files.clear()

        dyn1 = dyn2py.DynamoFile(f"{INPUT_DIR}/python_nodes.dyn")
        dyn2 = dyn2py.DynamoFile(f"{INPUT_DIR}/single_node.dyn")

        self.assertEqual(dyn1,
                         dyn2py.DynamoFile.get_open_file_by_uuid("3c3b4c05-9716-4e93-9360-ca0637cb5486"))
        self.assertEqual(dyn2,
                         dyn2py.DynamoFile.get_open_file_by_uuid("76de5c79-17c5-4c74-9f90-ad99a213d339"))

    def test_get_related_python_files(self):
        cleanup_output_dir()

        opt = dyn2py.Options(python_folder=OUTPUT_DIR)
        dyn1 = dyn2py.DynamoFile(f"{INPUT_DIR}/python_nodes.dyn")
        dyn2 = dyn2py.DynamoFile(f"{INPUT_DIR}/single_node.dyn")
        for dyn in [dyn1, dyn2]:
            dyn.extract_python(options=opt)
            for f in dyn2py.PythonFile.open_files:
                f.write()
            dyn2py.PythonFile.open_files.clear()

        python_files1 = dyn1.get_related_python_files(options=opt)
        python_files2 = dyn2.get_related_python_files(options=opt)

        self.assertEqual(len(python_files1), 6)
        self.assertEqual(len(python_files2), 1)

        no_python_files = dyn1.get_related_python_files()

        self.assertFalse(no_python_files)

    def test_write_same(self):
        cleanup_output_dir()

        shutil.copy(f"{INPUT_DIR}/python_nodes.dyn",
                    f"{OUTPUT_DIR}/python_nodes.dyn")

        new_dyn = dyn2py.DynamoFile(f"{OUTPUT_DIR}/python_nodes.dyn")
        new_dyn.modified = True
        new_dyn.write()

        with open(f"{INPUT_DIR}/python_nodes.dyn", "r", encoding="utf-8") as file1,\
                open(f"{OUTPUT_DIR}/python_nodes.dyn", "r", encoding="utf-8") as file2:
            json1 = json.load(file1, use_decimal=True)
            json2 = json.load(file2, use_decimal=True)

            self.assertEqual(json1, json2)

    def test_update_and_write(self):

        extract_single_node_dyn(modify_py=True)

        # Create a copy to update it:
        shutil.copy(f"{INPUT_DIR}/single_node.dyn",
                    f"{OUTPUT_DIR}/single_node.dyn")

        # Read back the modified py, and update:
        py = dyn2py.PythonFile(f"{OUTPUT_DIR}/single_node_mod.py")
        node1 = dyn2py.PythonNode(python_file=py)
        dyn1 = dyn2py.DynamoFile(f"{OUTPUT_DIR}/single_node.dyn")
        dyn1.update_python_node(node1)

        self.assertTrue(dyn1.modified)
        self.assertIn(node1, dyn1.python_nodes)

        # Save the file:
        dyn1.write()
        dyn2py.DynamoFile.open_files.clear()

        shutil.copy(f"{OUTPUT_DIR}/single_node.dyn",
                    f"{OUTPUT_DIR}/single_node2.dyn")

        # Check if the node in the copy:
        dyn2 = dyn2py.DynamoFile(f"{OUTPUT_DIR}/single_node2.dyn")
        node2 = dyn2.get_python_node_by_id(node_id=node1.id)

        self.assertTrue(node2)
        self.assertEqual(node1.checksum, node2.checksum)

        with self.assertRaises(dyn2py.PythonNodeNotFoundException):
            node2.id = "wrong_id"
            dyn2.update_python_node(node2)
