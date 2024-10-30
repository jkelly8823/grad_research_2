import sys
import io
import flawfinder
import tempfile
import os

def make_tmpfile(code_sample: str, file_suffix: str) -> str:
    # Create a temporary file to store the code sample
    with tempfile.NamedTemporaryFile(suffix=file_suffix, delete=False, mode='w', encoding='utf-8') as temp_file:
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

# with open(r"D:\grad_research_2\datasets\test\sample.cpp","r") as file:
#     tmp = file.read()
#     output = go_flawfinder(tmp,".cpp")
#     print(output)

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
# test_code_ext = ".cpp"
# output = go_flawfinder(test_code_snip, test_code_ext)
# print(output)