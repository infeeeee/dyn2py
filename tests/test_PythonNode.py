import unittest
import dyn2py
import hashlib
from tests.support import *


class TestPythonNode(unittest.TestCase):

    def test_init_from_dyn(self):
        dyn = dyn2py.DynamoFile(f"{INPUT_DIR}/single_node.dyn")
        node_dict = next((n for n in dyn.full_dict["Nodes"]
                          if n["NodeType"] == "PythonScriptNode"), {})

        # Found a node:
        self.assertTrue(node_dict)

        node_views = dyn.full_dict["View"]["NodeViews"]

        node = dyn2py.PythonNode(
            node_dict_from_dyn=node_dict,
            full_nodeviews_dict_from_dyn=node_views,
            source_dynamo_file=dyn
        )

        self.assertEqual(node.id, "1c5d99792882409e97e132b3e9f814b0")
        self.assertEqual(node.engine, "CPython3")
        self.assertEqual(node.checksum, "ec2c85a11ddbf8375da03f11272d427a")
        self.assertEqual(node.name, "Python Script")
        self.assertEqual(
            node.filename, "single_node_1c5d99792882409e97e132b3e9f814b0.py")

    def test_init_from_py(self):

        extract_single_node_dyn()

        # Open the extracted file and replace a string:
        with open(f"{OUTPUT_DIR}/single_node_1c5d99792882409e97e132b3e9f814b0.py") as orig_py, \
                open(f"{OUTPUT_DIR}/single_node_mod.py", "w") as mod_py:
            for line in orig_py:
                if "asd_string" in line:
                    line = line.replace("asd_string", "qwe_string")
                mod_py.write(line)

        py = dyn2py.PythonFile(f"{OUTPUT_DIR}/single_node_mod.py")
        
        node = dyn2py.PythonNode(
            node_id=py.header_data["py_id"],
            engine=py.header_data["py_engine"],
            code=py.code,
            checksum=hashlib.md5(py.code.encode()).hexdigest()
        )

        self.assertEqual(node.id, "1c5d99792882409e97e132b3e9f814b0")
        self.assertEqual(node.engine, "CPython3")
        self.assertEqual(node.checksum, "8d9091d24788a6fdfa5e1e109298b50e")
        