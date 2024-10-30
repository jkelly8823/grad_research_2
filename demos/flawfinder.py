import subprocess
import tempfile
import os

def run_flawfinder(code_sample: str) -> str:
    # Create a temporary file to store the code sample
    with tempfile.NamedTemporaryFile(suffix=".c", delete=False) as temp_file:
        temp_file.write(code_sample.encode('utf-8'))
        temp_file_path = temp_file.name

    try:
        # Run flawfinder on the temporary file and capture the output
        result = subprocess.run(
            ["flawfinder", temp_file_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        # Return any error messages from flawfinder
        return f"Error: {e.stderr}"
    finally:
        # Ensure the temporary file is deleted
        os.remove(temp_file_path)





output = run_flawfinder(r"D:\grad_research_2\datasets\test")
print(output)
