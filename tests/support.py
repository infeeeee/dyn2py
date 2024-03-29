import pathlib
import dyn2py

INPUT_DIR = "tests/input_files"
OUTPUT_DIR = "tests/output_files"
TEMP_DIR = "tests/temp_files"


def cleanup_dirs():
    for p in [OUTPUT_DIR, TEMP_DIR]:
        the_dir = pathlib.Path(p)
        if the_dir.exists():
            for f in the_dir.iterdir():
                f.unlink()
        else:
            the_dir.mkdir()


def extract_single_node_dyn(modify_py: bool = False):
    """Extract python from single_node.dyn
        File will be here: f"{OUTPUT_DIR}/single_node_1c5d99792882409e97e132b3e9f814b0.py"
        Modified file will be here: f"{OUTPUT_DIR}/single_node_mod.py"

    Args:
        modify_py (bool, optional): Also do some changes on the exported file. Defaults to False.

    """
    cleanup_dirs()

    # Extract py:
    options = dyn2py.Options(python_folder=OUTPUT_DIR)
    dyn = dyn2py.DynamoFile(f"{INPUT_DIR}/single_node.dyn")
    pythonfiles = dyn.extract_python(options)
    pythonfiles[0].write()

    dyn2py.File.open_files.clear()

    if modify_py:
        # Open the extracted file and replace a string:
        with open(f"{OUTPUT_DIR}/single_node_1c5d99792882409e97e132b3e9f814b0.py") as orig_py, \
                open(f"{OUTPUT_DIR}/single_node_mod.py", "w") as mod_py:
            for line in orig_py:
                if "asd_string" in line:
                    line = line.replace("asd_string", "qwe_string")
                mod_py.write(line)



