import unittest
import dyn2py
import pathlib
import platform

from tests.support import *


class TestFile(unittest.TestCase):

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

    def test_init_newfile(self):
        paths = [
            f"{INPUT_DIR}/new_file.dyn",
            pathlib.Path(f"{INPUT_DIR}/new_file.dyn")
        ]

        if platform.system() == "Windows":
            paths.extend([
                fr"{INPUT_DIR}\new_file.dyn",
                pathlib.Path(fr"{INPUT_DIR}\new_file.dyn")
            ])

        for path in paths:
            the_file = dyn2py.File(path)

            self.assertEqual(the_file.filepath,
                             pathlib.Path(f"{INPUT_DIR}/new_file.dyn"))
            self.assertEqual(the_file.basename, "new_file")
            self.assertEqual(the_file.dirpath, pathlib.Path(INPUT_DIR))
            self.assertEqual(the_file.realpath, pathlib.Path(path).resolve())

            self.assertEqual(the_file.mtime, 0.0)
            self.assertEqual(the_file.mtimeiso, "")
            self.assertFalse(the_file.exists)
            self.assertEqual(the_file.extension, ".dyn")
            self.assertFalse(the_file.modified)

    def test_newer(self):
        # Touch a file, so it will be always newer than the others:
        touched_file = pathlib.Path(f"{OUTPUT_DIR}/touched_file.py")
        touched_file.touch()
        newer_file = dyn2py.File(touched_file)

        older_file = dyn2py.File(f"{INPUT_DIR}/python_nodes.dyn")
        nonexisting_file = dyn2py.File(f"{INPUT_DIR}/new_file.dyn")

        self.assertTrue(newer_file.is_newer(older_file))
        self.assertTrue(newer_file.is_newer(nonexisting_file))

        self.assertFalse(older_file.is_newer(newer_file))
        self.assertTrue(older_file.is_newer(nonexisting_file))

        self.assertFalse(nonexisting_file.is_newer(older_file))
        self.assertFalse(nonexisting_file.is_newer(newer_file))

    def test_write(self):
        existing_file = dyn2py.File(f"{INPUT_DIR}/python_nodes.dyn")
        nonexisting_file = dyn2py.File(f"{INPUT_DIR}/new_file.dyn")
        options = dyn2py.Options()

        with self.assertRaises(TypeError):
            existing_file.write(options)

        with self.assertRaises(TypeError):
            nonexisting_file.write(options)

    def test_is_file(self):

        extract_single_node_dyn()

        paths = [
            (f"{INPUT_DIR}/python_nodes.dyn", "dyn"),
            (f"{OUTPUT_DIR}/single_node_1c5d99792882409e97e132b3e9f814b0.py", "py"),
            (f"README.md", ""),
        ]

        for path, f in paths:
            file = dyn2py.File(path)
            
            self.assertEqual(file.is_dynamo_file(), f=="dyn")
            self.assertEqual(file.is_python_file(), f=="py")

            
