# TOOLRAG Setup and Configuration

This project utilizes various API keys and configuration options stored in a `.env` file for easy environment setup and secure management of sensitive information.

## Configuring .env

### Model API Keys

The project requires API keys for the following services:

- **Anthropic API Key**: `ANTHROPIC_API_KEY`
- **OpenAI API Key**: `OPENAI_API_KEY`

These keys are used for querying AI models hosted by Anthropic and OpenAI.

### LangChain Tracing Variables

To enable tracing and monitoring within the LangChain framework, the following environment variables are required:

- **LangChain Endpoint**: `LANGCHAIN_ENDPOINT`
- **LangChain API Key**: `LANGCHAIN_API_KEY`
- **LangChain Project Name**: `LANGCHAIN_PROJECT`
- **Enable Tracing**: `LANGCHAIN_TRACING_V2`

### Semgrep Configuration

The project integrates with Semgrep for static analysis, requiring the following token:

- **Semgrep App Token**: `SEMGREP_APP_TOKEN`

### RAG Knowledge Base and Output Paths

The project also allows configuration of paths for data sources and outputs:

- **CWE Source File**: `CWE_SRC` – Location of the CWE XML file to build the RAG knowledge base.
- **RAG Knowledge Base Directory**: `RAG_PERSIST` – Directory to persist RAG knowledge base.
- **Recursion Limit for RAG**: `RAG_RECURSION_LIMIT`
- **Output Path**: `OUTPUT_PTH` – Directory to save run outputs.

### Model Source and Model Names

Specify the model source and particular models for various functionalities:

- **Model Source**: `MODEL_SRC` (e.g., `Anthropic`)
- **SAST Model**: `ANTHROPIC_SAST_MODEL`
- **Summarization Model**: `ANTHROPIC_SUMMARIZE_MODEL`
- **Analysis Model**: `ANTHROPIC_ANALYSIS_MODEL`
- **RAG Model**: `ANTHROPIC_RAG_MODEL`

### Token Limits

Specify the maximum accepted token length for code samples

- **SAMPLE_TOKEN_LIMIT**: `TOKEN_LIMIT`

## Setting Up the Environment

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/jkelly8823/toolrag_src
    cd toolrag_src

2. **Install Python Dependencies**: Make sure to install all required dependencies as specified in the project’s requirements.txt file
    ```bash
    pip install -r requirements.txt
    ```
3. **Install External Dependencies**: Make sure to install all required dependencies for Static Analysis
- Docker
- Flawfinder
- CppCheck
- AppInspector
- Semgrep

4. **Set Up the .env File**: Create a .env file in the project root and populate it with the necessary API keys and paths, as shown above. Alternatively, copy the existing sample
    ```bash
    cp .env.example .env
    ```
5. **Verify API Keys and Paths**: Ensure all necessary keys and file paths are set correctly. Incomplete or incorrect configurations may lead to errors during runtime

## Running the Project
To start the project, use the main script ```runners\toolrag.py```
    ```bash
    py .\runners\toolrag.py
    ```

## Additional Information
# Model Selection
The ```.env``` file allows flexibility in choosing between different model sources (OpenAI or Anthropic). Ensure that the selected model configurations align with the source specified in MODEL_SRC. This setup supports various model tasks, including:
- Static analysis and security testing
- Summarization
- Code analysis
- Retrieval-augmented generation

# Knowledge Base and Output Directories
The configuration includes settings for constructing a RAG knowledge base from a CWE XML file, as well as specifying a directory to save processed output data. Ensure these paths are accessible and writable.

# Troubleshooting
If you encounter issues:
- **Check API Key Validity**: Ensure that all API keys are up to date and have sufficient permissions.
- **Verify Paths**: Double-check that all paths in the .env file point to the correct files and directories.
- **Contact Support**: For further assistance, refer to the project’s issue tracker or support channels, or reach out to the author.