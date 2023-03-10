import pathlib

INPUT_DIR = "tests/input_files"
OUTPUT_DIR = "tests/output_files"

def cleanup_output_dir():
    output_dir = pathlib.Path(OUTPUT_DIR)
    if output_dir.exists():
        for f in output_dir.iterdir():
            f.unlink()
    else:
        output_dir.mkdir()
