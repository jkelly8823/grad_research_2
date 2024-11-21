import os
import subprocess
from dotenv import load_dotenv
load_dotenv()

# Step 1: Start the persistent SEMGREP container
subprocess.run(
    [
        "docker", "run", "-d",
        "--name", "semgrep-container",
        "-e", f"SEMGREP_APP_TOKEN={os.getenv('SEMGREP_APP_TOKEN')}",
        "-v", "D:/grad_research_2:/src",
        "semgrep/semgrep",
        "sleep", "infinity"
    ],
    check=True
)

try:
    # Step 2: Execute SEMGREP scan via docker exec
    temp_file_path = r"D:\grad_research_2\datasets\tst\primevul_219912.c"  # Path relative to the mounted directory
    container_temp_file_path = r"/src/datasets/tst/primevul_219912.c"

    result = subprocess.run(
        [
            "docker", "exec", "semgrep-container",
            "semgrep", "scan",
            "--config=r/all",
            container_temp_file_path
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    print(result.stdout)

finally:
    # Step 3: Stop and remove the container
    subprocess.run(["docker", "stop", "semgrep-container"], check=True)
    subprocess.run(["docker", "rm", "semgrep-container"], check=True)
