import subprocess
import requests
import time

def run_sonarqube_scan(sonarqube_url, project_key, token, source_dir):
    """
    Run a SonarQube scan on the specified source directory.
    
    :param sonarqube_url: The base URL of the SonarQube server.
    :param project_key: The project key in SonarQube for which the scan will run.
    :param token: The SonarQube API token for authentication.
    :param source_dir: The directory containing source code to scan.
    :return: Analysis report or error message.
    """
    try:
        # Step 1: Run SonarQube Scanner on the source directory
        command = [
            r"D:\grad_research_2\sonar-scanner-cli\bin\sonar-scanner.bat",
            f"-Dsonar.projectKey={project_key}",
            f"-Dsonar.sources={source_dir}",
            f"-Dsonar.host.url={sonarqube_url}",
            f"-Dsonar.login={token}"
        ]
        print(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            return f"Error during scan: {result.stderr}"

        print("Scan triggered successfully.")

        # Step 2: Monitor scan status
        analysis_url = f"{sonarqube_url}/api/ce/component"
        params = {"component": project_key}
        headers = {"Authorization": f"Basic {token}"}

        print("Monitoring scan status...")
        while True:
            response = requests.get(analysis_url, params=params, headers=headers)
            response.raise_for_status()
            task = response.json().get("current")
            
            if task["status"] == "SUCCESS":
                print("Scan completed successfully.")
                break
            elif task["status"] == "FAILED":
                return "SonarQube analysis failed."
            
            print("Scan in progress...")
            time.sleep(5)  # wait before checking status again

        # Step 3: Retrieve analysis results (e.g., issues found)
        issues_url = f"{sonarqube_url}/api/issues/search"
        params = {"componentKeys": project_key}
        response = requests.get(issues_url, params=params, headers=headers)
        response.raise_for_status()

        issues = response.json().get("issues", [])
        if issues:
            output = "Analysis Report:\n"
            for issue in issues:
                output += (
                    f"Issue: {issue['message']}, Severity: {issue['severity']}, "
                    f"File: {issue['component']}, Line: {issue.get('line', 'N/A')}\n"
                )
            return output
        else:
            return "No issues found."

    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == "__main__":
    sonarqube_url = "http://localhost:9000"  # Replace with your SonarQube server URL
    project_key = "sq_tests"  # Replace with your SonarQube project key
    token = "sqp_f4c6630713f0583caa5dfeaff58e3d8e57d4066b"  # Replace with your SonarQube API token
    source_dir = r"datasets"  # Replace with the path to your source code

    results = run_sonarqube_scan(sonarqube_url, project_key, token, source_dir)
    print(results)
