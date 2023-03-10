import unittest
import subprocess


class TestCommandLine(unittest.TestCase):
    def test_help(self):

        args = ["-h", "--help"]

        for arg in args:
            p = subprocess.run(f"dyn2py {arg}",
                               capture_output=True, shell=True)

            # No error:
            self.assertFalse(p.stderr)
