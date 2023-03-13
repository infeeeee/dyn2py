import unittest
import dyn2py
import pathlib
import platform

from tests.support import *


class TestFile(unittest.TestCase):

    # Write methods should be tested in subclasses!

    def test_init(self):
        paths = [
            f"{INPUT_DIR}/python_nodes.dyn",
            pathlib.Path(f"{INPUT_DIR}/python_nodes.dyn")
        ]

        if platform.system() == "Windows":
            paths.extend([
                fr"{INPUT_DIR}\python_nodes.dyn",
                pathlib.Path(fr"{INPUT_DIR}\python_nodes.dyn")
            ])

        for path in paths:
            the_file = dyn2py.File(path)

            self.assertEqual(the_file.filepath,
                             pathlib.Path(f"{INPUT_DIR}/python_nodes.dyn"))
            self.assertEqual(the_file.basename, "python_nodes")
            self.assertEqual(the_file.dirpath, pathlib.Path(INPUT_DIR))
            self.assertEqual(the_file.realpath, pathlib.Path(path).resolve())

            self.assertTrue(the_file.exists)
            self.assertEqual(the_file.extension, ".dyn")
            self.assertFalse(the_file.modified)

            self.assertIs(type(the_file), dyn2py.DynamoFile)

    def test_init_newfile(self):
        paths = [
            f"{INPUT_DIR}/new_file.py",
            pathlib.Path(f"{INPUT_DIR}/new_file.py")
        ]

        if platform.system() == "Windows":
            paths.extend([
                fr"{INPUT_DIR}\new_file.py",
                pathlib.Path(fr"{INPUT_DIR}\new_file.py")
            ])

        for path in paths:
            the_file = dyn2py.File(path)

            self.assertEqual(the_file.filepath,
                             pathlib.Path(f"{INPUT_DIR}/new_file.py"))
            self.assertEqual(the_file.basename, "new_file")
            self.assertEqual(the_file.dirpath, pathlib.Path(INPUT_DIR))
            self.assertEqual(the_file.realpath, pathlib.Path(path).resolve())

            self.assertEqual(the_file.mtime, 0.0)
            self.assertEqual(the_file.mtimeiso, "")
            self.assertFalse(the_file.exists)
            self.assertEqual(the_file.extension, ".py")
            self.assertFalse(the_file.modified)

            self.assertEqual(the_file.__class__, dyn2py.PythonFile)

    def test_newer(self):
        older_file = dyn2py.File(f"{INPUT_DIR}/single_node.dyn")
        nonexisting_file = dyn2py.File(f"{INPUT_DIR}/new_file.py")

        # Extract a python file so it is always newer than the others:
        cleanup_output_dir()
        opt = dyn2py.Options(python_folder=OUTPUT_DIR)
        older_file.extract_python(options=opt)  # type: ignore
        newer_file = dyn2py.File(
            f"{OUTPUT_DIR}/single_node_1c5d99792882409e97e132b3e9f814b0.py")

        self.assertTrue(newer_file.is_newer(older_file))
        self.assertTrue(newer_file.is_newer(nonexisting_file))

        self.assertFalse(older_file.is_newer(newer_file))
        self.assertTrue(older_file.is_newer(nonexisting_file))

        self.assertFalse(nonexisting_file.is_newer(older_file))
        self.assertFalse(nonexisting_file.is_newer(newer_file))

    def test_is_file(self):

        extract_single_node_dyn()

        paths = [
            (f"{INPUT_DIR}/python_nodes.dyn", "dyn"),
            (f"{OUTPUT_DIR}/single_node_1c5d99792882409e97e132b3e9f814b0.py", "py"),
            (f"README.md", ""),
        ]

        for path, f in paths:
            file = dyn2py.File(path)

            self.assertEqual(file.is_dynamo_file(), f == "dyn")
            self.assertEqual(file.is_python_file(), f == "py")
