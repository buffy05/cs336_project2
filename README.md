# Project 2: Natural Language Database Access with Local LLM

## Team Members

*   Saksham Mehta [sm2683]
*   ...

## Contributions


## How to Run

1.  **Prerequisites:**
    *   Access to Rutgers ILAB machines (with PostgreSQL configured for your NetID)
    *   Required Python packages: `pip install llama-cpp-python paramiko pandas psycopg2-binary`
    *   On macOS, for GPU acceleration  Install `llama-cpp-python` with Metal support: `CMAKE_ARGS=\"-DLLAMA_METAL=on\" pip install -U llama-cpp-python --no-cache-dir`
2.  **Setup:**
    *   Download the LLM model file (`Phi-3.5-mini-instruct-Q4_K_M.gguf`) from the link in `Project_2.txt` and place it in the same directory as `database_llm.py`, or update the `MODEL_PATH` variable in `database_llm.py`.
    *   Copy the `ilab_script.py` to your home directory on your ILAB account (e.g., using `scp ilab_script.py your_netid@ilab.cs.rutgers.edu:~/`). Ensure it has execute permissions if needed, though `python3 ~/ilab_script.py ...` should work.
    *   Ensure your PostgreSQL database is set up on `postgres.cs.rutgers.edu` with the tables defined in `schema.sql`.
3.  **Execution:**
    *   Run the local script: `python3 database_llm.py`
    *   Enter your ILAB NetID and SSH password when prompted.
    *   Enter your natural language questions about the database.
    *   Type `exit` to quit.

## Challenges


## Interesting Findings

## Extra Credit


## LLM Chat Transcripts

*   [Link]