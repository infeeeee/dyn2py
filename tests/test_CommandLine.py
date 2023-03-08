import unittest
import subprocess
import platform


class TestCommandLine(unittest.TestCase):
    def test_help(self):
        args = ["-h", "--help"]
        readme_help_lines = []

        # Read help from readme:
        with open("README.md", mode="r", encoding="utf-8") as readme:
            is_help_line = False

            for line in readme.readlines():
                line_text = line.rstrip()

                if line_text == "> dyn2py --help":
                    is_help_line = True
                elif is_help_line and line_text == "```":
                    # It's the end of the help
                    break
                elif is_help_line:
                    readme_help_lines.append(line_text)

        # Check if readme was read at all:
        self.assertTrue(readme_help_lines)

        # Cannot set terminal columns on windows, so simply skip this:
        if not platform.system() == "Windows":
            for arg in args:
                p = subprocess.run(
                    ["dyn2py", arg], capture_output=True, shell=True)
                output_help = p.stdout.decode()
                output_help_lines = output_help.split("\n")

                self.assertEqual(
                    output_help.count("\n"),
                    len(readme_help_lines))

                for i, l in enumerate(readme_help_lines):
                    self.assertEqual(l, output_help_lines[i])
