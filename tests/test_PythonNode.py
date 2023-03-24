import unittest
import dyn2py

from tests.support import *


class TestPythonNode(unittest.TestCase):

    def test_init_from_dyn(self):
        dyn = dyn2py.DynamoFile(f"{INPUT_DIR}/single_node.dyn")
        node_dict = next((n for n in dyn.full_dict["Nodes"]
                          if n["NodeType"] == "PythonScriptNode"), {})

        # Found a node:
        self.assertTrue(node_dict)

        node = dyn2py.PythonNode(
            node_dict_from_dyn=node_dict,
            dynamo_file=dyn
        )

        self.assertEqual(node.id, "1c5d99792882409e97e132b3e9f814b0")
        self.assertEqual(node.engine, "CPython3")
        self.assertEqual(node.checksum, "92d46019bf538072db6bd1287267c147")
        self.assertEqual(node.name, "Python Script")
        self.assertEqual(
            node.filename, "single_node_1c5d99792882409e97e132b3e9f814b0.py")

    def test_init_from_py(self):

        extract_single_node_dyn(modify_py=True)

        py = dyn2py.PythonFile(f"{OUTPUT_DIR}/single_node_mod.py")

        node = dyn2py.PythonNode(python_file=py)

        self.assertEqual(node.id, "1c5d99792882409e97e132b3e9f814b0")
        self.assertEqual(node.engine, "CPython3")
        self.assertEqual(node.checksum, "64a73c52bd213b6f1b593697cdde789b")

    def test_init_exception(self):

        dyn = dyn2py.DynamoFile(f"{INPUT_DIR}/single_node.dyn")
        node_dict = next((n for n in dyn.full_dict["Nodes"]
                          if n["NodeType"] == "PythonScriptNode"), {})

        extract_single_node_dyn(modify_py=True)

        py = dyn2py.PythonFile(f"{OUTPUT_DIR}/single_node_mod.py")

        with self.assertRaises(dyn2py.PythonNodeException):
            node1 = dyn2py.PythonNode(
                node_dict_from_dyn=node_dict,
                dynamo_file=dyn,
                python_file=py
            )

            node2 = dyn2py.PythonNode()
