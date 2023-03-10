import pathlib
import dyn2py

INPUT_DIR = "tests/input_files"
OUTPUT_DIR = "tests/output_files"

def cleanup_output_dir():
    output_dir = pathlib.Path(OUTPUT_DIR)
    if output_dir.exists():
        for f in output_dir.iterdir():
            f.unlink()
    else:
        output_dir.mkdir()


def extract_single_node_dyn():
    """Extract python from single_node.dyn
        File will be here: f"{OUTPUT_DIR}/single_node_1c5d99792882409e97e132b3e9f814b0.py"
    """
    cleanup_output_dir()

    # Extract py:
    options = dyn2py.Options(python_folder=OUTPUT_DIR)
    dyn = dyn2py.DynamoFile(f"{INPUT_DIR}/single_node.dyn")
    dyn.extract_python(options)
