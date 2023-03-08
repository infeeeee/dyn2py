import unittest
import dyn2py
import pathlib

INPUT_DIR = "tests/input_files"
OUTPUT_DIR = "tests/output_files"

def cleanup_output_dir():
    output_dir = pathlib.Path(OUTPUT_DIR)
    if output_dir.exists():
        for f in output_dir.iterdir():
            f.unlink()
    else:
        output_dir.mkdir()

class TestDynamoFile(unittest.TestCase):

    # Missing methods:
    # get_related_python_files
    # get_open_file_by_uuid
    # update_python_node
    # write

    def test_read(self):
        dyn = dyn2py.DynamoFile(f"{INPUT_DIR}/python_nodes.dyn")
        dyn.read()

        self.assertEqual(dyn.uuid, "3c3b4c05-9716-4e93-9360-ca0637cb5486")
        self.assertEqual(dyn.name, "python_nodes")
        self.assertTrue(dyn in dyn.open_files)

        with self.assertRaises(dyn2py.DynamoFileException):
            dyn1 = dyn2py.DynamoFile(f"{INPUT_DIR}/dynamo1file.dyn")
            dyn1.read()

        with self.assertRaises(FileNotFoundError):
            dyn2 = dyn2py.DynamoFile(f"{INPUT_DIR}/not_existing.dyn")
            dyn2.read()
            

    def test_get_python_node(self):
        dyn = dyn2py.DynamoFile(f"{INPUT_DIR}/python_nodes.dyn")
        py_nodes = dyn.get_python_nodes()
        py_node = dyn.get_python_node_by_id("d7704617c75e4bf1a5c387b7c3f001ea")

        self.assertEqual(len(py_nodes), 6)
        self.assertTrue(py_node)
        self.assertTrue(py_node in py_nodes)
        self.assertEqual(py_node.checksum, "1f3d9e6153804fe1ed37571a9cda8e26")

        with self.assertRaises(dyn2py.PythonNodeNotFoundException):
            dyn.get_python_node_by_id("wrongid")

    def test_extract_python(self):
        cleanup_output_dir()

        opt = dyn2py.Options(python_folder=OUTPUT_DIR)
        dyn = dyn2py.DynamoFile(f"{INPUT_DIR}/python_nodes.dyn")
        dyn.extract_python(options=opt)

        output_dir = pathlib.Path(OUTPUT_DIR)
        self.assertEqual(len(list(output_dir.iterdir())), 6)
