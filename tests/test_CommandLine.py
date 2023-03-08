import unittest
import subprocess


class TestCommandLine(unittest.TestCase):
    def test_help(self):
        args = ["-h", "--help"]
        readme_help_lines = []

        # Read help from readme:
        with open("README.md", mode="r", encoding="utf-8") as readme:
            is_help_line = False

            for line in readme.readlines():
                if line == "> dyn2py --help":
                    is_help_line = True
                elif is_help_line and line == "```":
                    # It's the end of the help
                    break
                elif is_help_line:
                    readme_help_lines.append(line)

        for arg in args:
            p = subprocess.run(
                ["dyn2py", arg], capture_output=True, shell=True)
            output_help = p.stdout.decode()
            output_help_lines = output_help.split("\n")

            self.assertEqual(output_help.count("\n"), len(readme_help_lines))
            for i, l in enumerate(readme_help_lines):
                self.assertEqual(l, output_help_lines[i])
