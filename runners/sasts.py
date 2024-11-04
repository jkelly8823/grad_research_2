import sys
import io
import flawfinder
import tempfile
import os
import subprocess

def make_tmpfile(code_sample: str, file_suffix: str) -> str:
    # Create a temporary file to store the code sample
    with tempfile.NamedTemporaryFile(suffix=file_suffix, dir='datasets/tmp', delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write(code_sample)
        temp_file_path = temp_file.name

    # print(temp_file_path)
    try:
       return temp_file_path
    except Exception as e:
        # Return any error messages from flawfinder
        return f"Error: {e}"

def go_flawfinder(code_sample: str, file_suffix: str) -> str:
    try:
        temp_file_path = make_tmpfile(code_sample, file_suffix)
        
        # print("Starting function")  # Debug statement

        # Save the original stdout and argv
        original_stdout = sys.stdout
        original_argv = sys.argv
        
        # Redirect stdout to capture output
        sys.stdout = io.StringIO()
        sys.argv = ["flawfinder", '-D', '-Q'] + [temp_file_path]  # Mimic command-line arguments

        # Print argv
        # print("Arguments:", sys.argv)

        # Print statements for debugging
        # print("Before calling flawfinder.main()")
        
        # Call the flawfind function directly
        if hasattr(flawfinder, "flawfind"):
            flawfinder.flawfind()
            # print("After calling flawfinder.flawfind()")  # This only appears if flawfind() runs successfully
        else:
            print("flawfinder does not have a 'flawfind' function.")
        
        # Capture the output from redirected stdout
        output = sys.stdout.getvalue()

        return output
    except Exception as e:
        return f"Error running flawfinder: {e}"
    finally:
        # Restore original stdout and sys.argv
        sys.stdout = original_stdout
        sys.argv = original_argv
        try:
            os.remove(temp_file_path)
        except Exception as e:
            print(f"Error deleting tmpfile: {e}")

def go_cppcheck(code_sample: str, file_suffix: str) -> str:
    try:
        # Create a temporary file with the code sample
        temp_file_path = make_tmpfile(code_sample, file_suffix)

        # Run cppcheck on the temporary file, capturing the output
        result = subprocess.run(
            ["cppcheck", "--enable=all", "--quiet", "--suppress=checkersReport",  "--template={file}:{line}: [{severity}] ({id}):\n\t {message}", temp_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        # Capture the output from cppcheck
        output = result.stdout
        return output

    except Exception as e:
        return f"Error running cppcheck: {e}"
    finally:
        # Clean up the temporary file
        try:
            os.remove(temp_file_path)
        except Exception as e:
            print(f"Error deleting tmpfile: {e}")

def go_appinspector(code_sample: str, file_suffix: str) -> str:
    try:
        # Create a temporary file with the code sample
        temp_file_path = make_tmpfile(code_sample, file_suffix)

        # Run appinspector on the temporary file, capturing the output
        result = subprocess.run(
            ["appinspector", "analyze", "-s", temp_file_path, "-f", "text", "-e", "%F:%L: [%S] (%N):\n\t%T\t%m\t%D", "-N", "-n", "--disable-console=False"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        # Capture the output from appinspector
        output = result.stdout
        split_str = '[Match Details]-------------------------------------------------------------------\n'
        match_details_start = output.rfind(split_str)
        if match_details_start != -1:
            # Extract the relevant part of the output after [Match Details]
            output = output[match_details_start+len(split_str):]
        return output

    except Exception as e:
        return f"Error running appinspector: {e}"
    finally:
        # Clean up the temporary file
        try:
            os.remove(temp_file_path)
        except Exception as e:
            print(f"Error deleting tmpfile: {e}")

def go_semgrep(code_sample: str, file_suffix: str) -> str:
    try:
        # Create a temporary file with the code sample
        temp_file_path = make_tmpfile(code_sample, file_suffix)

        # Run semgrep on the temporary file, capturing the output
        result = subprocess.run(
            # Submit Scan Online too, use online ruleset
            # ["docker", "run", "-e", "SEMGREP_APP_TOKEN=e15c0a35ea4e33b27a298fa14a1ca193cad729702f5c68c72451f2a832acab32", "--rm", "-v", "D:/grad_research_2:/src", "semgrep/semgrep", "semgrep", "ci", "--quiet", "--subdir", "datasets/tst"],
            # Local only, use local ruleset (?)
            ["docker", "run", "-e", "SEMGREP_APP_TOKEN=e15c0a35ea4e33b27a298fa14a1ca193cad729702f5c68c72451f2a832acab32", "--rm", "-v", "D:/grad_research_2:/src", "semgrep/semgrep", "semgrep", "scan", "--config=r/all", "--quiet", "datasets/tst"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        # Capture the output from semgrep
        output = result.stdout
        split_str = '└─────────────────┘'
        match_details_start = output.find(split_str)
        if match_details_start != -1:
            # Extract the relevant part of the output after [# of findings]
            output = output[match_details_start+len(split_str)+2:]
        return output

    except Exception as e:
        return f"Error running semgrep: {e}"
    finally:
        # Clean up the temporary file
        try:
            os.remove(temp_file_path)
        except Exception as e:
            print(f"Error deleting tmpfile: {e}")



# test_code_snip = (
#     "void calculateDiscountedPrice(char *userInput, int itemPrice, float discountRate) {\n"
#     "    char buffer[10];\n"
#     "    int discountedPrice;\n"
#     "    float discountAmount;\n"
#     "    if (isLoggedIn) {\n"
#     "        strcpy(buffer, userInput);\n"
#     "        discountAmount = (itemPrice * discountRate) / 100;\n"
#     "        discountedPrice = itemPrice - (int)discountAmount;\n"
#     "        sprintf(buffer, \"Discounted Price: %d\", discountedPrice);\n"
#     "        printf(\"%s\\n\", buffer);\n"
#     "    } else {\n"
#     "        printf(\"User is not logged in.\\n\");\n"
#     "    }\n"
# "}\n"
# )
# print(go_flawfinder(test_code_snip,'.cpp'))
# print("~"*30)
# print(go_cppcheck(test_code_snip,'.cpp'))
# print("~"*30)
# print(go_appinspector(test_code_snip,'.cpp'))
# print("~"*30)
# print(go_semgrep(test_code_snip,'.cpp'))

# docker run --rm -it -v D:\grad_research_2\datasets\test:/tmp -v $(pwd):/app:rw -w /app -t ghcr.io/joernio/joern joern
# docker run -e SEMGREP_APP_TOKEN=e15c0a35ea4e33b27a298fa14a1ca193cad729702f5c68c72451f2a832acab32 --rm -v "D:/grad_research_2:/src" semgrep/semgrep semgrep ci --subdir datasets/tst
# docker run -e SEMGREP_APP_TOKEN=e15c0a35ea4e33b27a298fa14a1ca193cad729702f5c68c72451f2a832acab32 --rm -v "D:/grad_research_2:/src" semgrep/semgrep semgrep scan --config=r/all --quiet datasets/tst
