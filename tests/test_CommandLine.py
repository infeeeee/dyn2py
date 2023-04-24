from __future__ import annotations
import unittest
import subprocess
import shutil
import pathlib

from tests.support import *


class TestCommandLine(unittest.TestCase):

    # Sources to test:          normal      dry_run     force       backup      filter      update      python_folder
    # - single dyn file         ✅          ✅          ✅          ✅                                    ✅
    # - multiple dyn files      ✅          ✅          ✅          ✅                                    ✅
    # - single python file
    # - multiple python files
    # - single folder
    # - multiple folders

    # Options to test:
    # dry run
    # force
    # backup
    # filter
    # update
    # python folder

    def test_help_and_version(self):

        args = ["-h", "--help", "-v", "--version"]

        for arg in args:
            p = subprocess.run(f"dyn2py {arg}",
                               capture_output=True, shell=True)

            self.assertFalse(p.stderr)

    dyn_sources = [
        {"filename": "python_nodes.dyn", "output_file_count": 6},
        {"filename": "single_node.dyn", "output_file_count": 1}
    ]

    py_sources = [
        {"filename": "single_node_mod.py"},
    ]

    dyn_sources_error = ["dynamo1file.dyn",
                         "no_python.dyn",
                         "nonexisting.dyn"]

    @staticmethod
    def run_command(args: list = []) -> dict:
        """_summary_

        Args:
            args (list, optional): list of arguments to run. Defaults to [].

        Returns:
            dict["stderr"]: error message
            dict["python_file_mtimes"]: exported file in the output dir, and modification times
        """
        argstring = " ".join(args)
        process = subprocess.run(f"dyn2py -l WARNING {argstring}",
                                 capture_output=True, shell=True)

        stderr = process.stderr.decode()

        python_files = {p: p.stat().st_mtime for p in pathlib.Path(OUTPUT_DIR).iterdir()
                        if p.suffix == ".py"}

        output = {
            "stderr": stderr,
            "python_file_mtimes": python_files
        }

        return output

    @staticmethod
    def generate_test_args(source_dicts: list[dict]) -> list[dict]:

        tests = []

        for i, source_dict in enumerate(source_dicts):
            for backup_arg in ["-b", "--backup"]:
                for force_arg in ["-F", "--force"]:
                    for pfolder_option in ["", "-p", "--python-folder"]:

                        test_dicts = [source_dict.copy()]

                        test_dicts[0]["filenames"] = [
                            test_dicts[0]["filename"]]
                        if i == 0 and len(source_dict) > 1:
                            # Create a multi file version on the first file:
                            d = {}
                            for key in source_dict:
                                if key == "filename":
                                    d["filenames"] = [f["filename"]
                                                      for f in source_dicts]
                                elif isinstance(source_dict[key], (int, float)):
                                    d[key] = sum([f[key]
                                                 for f in source_dicts])
                            test_dicts.append(d)

                        for test_dict in test_dicts:

                            if pfolder_option:
                                file_dir = TEMP_DIR
                                pfolder_arg = f"{pfolder_option} {OUTPUT_DIR}"
                            else:
                                file_dir = OUTPUT_DIR
                                pfolder_arg = ""

                            test_dict["filepath"] = " ".join(
                                [f"{file_dir}/{f}" for f in test_dict["filenames"]])

                            test_dict.update({
                                "pfolder_arg": pfolder_arg,
                                "backup_arg": backup_arg,
                                "force_arg": force_arg
                            })

                            tests.append(test_dict)

        return tests

    def test_dyn_error(self):
        for s in self.dyn_sources_error:

            cleanup_dirs()

            if pathlib.Path(f"{INPUT_DIR}/{s}").exists():
                shutil.copy(f"{INPUT_DIR}/{s}",
                            f"{OUTPUT_DIR}/{s}")

            file_open = self.run_command(
                [f"{OUTPUT_DIR}/{s}"])

            self.assertTrue(bool(file_open["stderr"]))
            self.assertEqual(
                len(file_open["python_file_mtimes"]), 0)

    def test_dyn(self):

        dyn_tests = self.generate_test_args(self.dyn_sources)

        for s in dyn_tests:
            cleanup_dirs()

            # if no pythonfolder, everything should be in output ddir
            if not s["pfolder_arg"]:
                source_dir = OUTPUT_DIR
            else:
                source_dir = TEMP_DIR

            # copy  source files:
            for filename in s["filenames"]:
                shutil.copy(f"{INPUT_DIR}/{filename}",
                            f"{source_dir}/{filename}")
            

            # Open files normally
            file_open = self.run_command(
                [s["pfolder_arg"], s['filepath']])

            # Open without error:
            self.assertFalse(
                bool(file_open["stderr"]), msg=file_open["stderr"])
            self.assertEqual(
                len(file_open["python_file_mtimes"]), s["output_file_count"])

            # Test no overwrite
            file_no_overwrite = self.run_command(
                [s["pfolder_arg"], s['filepath']])

            # Should give error, because they already exist:
            self.assertTrue(bool(file_no_overwrite["stderr"]))
            self.assertEqual(
                len(file_no_overwrite["python_file_mtimes"]), s["output_file_count"])

            # The modify time shouldn't change as they were not overwritten:
            for p in file_no_overwrite["python_file_mtimes"]:
                self.assertEqual(
                    file_no_overwrite["python_file_mtimes"][p], file_open["python_file_mtimes"][p])

            # Test force:
            file_force = self.run_command(
                [s["pfolder_arg"], s["force_arg"], s['filepath']])

            # Should not have an error:
            self.assertFalse(bool(file_force["stderr"]))
            self.assertEqual(
                len(file_force["python_file_mtimes"]), s["output_file_count"])

            # Modify time should be higher as they were replaced
            for p in file_force["python_file_mtimes"]:
                self.assertTrue(
                    file_force["python_file_mtimes"][p] > file_open["python_file_mtimes"][p]
                )

            # Test backup
            file_backup = self.run_command(
                [s["pfolder_arg"], s["force_arg"], s["backup_arg"], s['filepath']])

            self.assertFalse(bool(file_backup["stderr"]))

            self.assertEqual(
                len(file_backup["python_file_mtimes"]
                    ), s["output_file_count"] * 2,
                msg=f""
            )

            for p in file_force["python_file_mtimes"]:
                self.assertTrue(
                    file_backup["python_file_mtimes"][p] > file_force["python_file_mtimes"][p]
                )

    # def test_py(self):
    #     py_tests = self.generate_test_args(self.py_sources)

    #     # TODO add more python files!
    #     self.assertEqual(len(py_tests), 1)

    #     for s in py_tests:
    #         cleanup_dirs()

    #         extract_single_node_dyn(modify_py=True)

            
    #         # if pythonfolder, python should be in the temp folder:
    #         if s["pfolder_arg"]:
    #             for filename in s["filenames"]:
    #                 shutil.move(f"{OUTPUT_DIR}/{filename}",
    #                             f"{TEMP_DIR}/{filename}")

    #         # Open files normally
    #         file_open = self.run_command(
    #             [s["pfolder_arg"], s['filepath']])


    #         # Open without error:
    #         self.assertFalse(
    #             bool(file_open["stderr"]), msg=file_open["stderr"])
    #         self.assertEqual(
    #             len(file_open["python_file_mtimes"]), s["output_file_count"])

                                

    def test_single_dyn_dryrun(self):
        for s in self.dyn_sources:
            for arg in ["-n", "--dry-run"]:

                cleanup_dirs()

                shutil.copy(f"{INPUT_DIR}/{s['filename']}",
                            f"{OUTPUT_DIR}/{s['filename']}")

                file_dryrun = self.run_command(
                    [arg, f"{OUTPUT_DIR}/{s['filename']}"])

                self.assertFalse(bool(file_dryrun["stderr"]))
                self.assertFalse(file_dryrun["python_file_mtimes"])
