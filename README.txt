# Project 2: Natural Language Database Access with Local LLM

## Team Members

*   Saksham Mehta [sm2683]
*   Soma Parvathini [svp98]
*   Syona Bhandari [sb2199]
*   Rhemie Patiak [rmp260]

## Contributions:  
   - The project was collaborated on by Soma, Syona, Saksham, and Rhemie. We all participated in meetings to fix and debug code. We all worked on all aspects of the code equally.

## How to Run:

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

## What we found challenging:  
   - **Parsing LLM output reliably**—the model sometimes wrapped the SQL in extra commentary, so our regex had to be very precise.  
   - **Balancing prompt length vs. model context window**—too much schema caused truncation, too little led to wrong table names.  
   - **Computing issues** - We were seeing slow runtimes at points of time with the ilab machines.

## What we found interesting:  
   - How small tweaks in the natural‐language prompt dramatically improved the correctness of generated SQL.  
   - Watching the local GGUF model reliably generate complex joins and aggregates without any hand-coding.  
   - Observing the performance trade-offs between model size and response latency.  

Extra credit:  
   - Yes, we implemented the extra credit requirement. We extended both `database_llm.py` and `ilab_script.py` to accept SQL via **stdin** when no command-line argument is provided.  


## AI Chat Transcripts

*   https://docs.google.com/document/d/1CFAws1-_1A5uBCMQDq9KI8AD-hdm8NKftl7_4Xd8lzk/edit?usp=sharing

## FrontEnd ExtraCredit: 
Frontend Features
The updated version of this project implements a fully functional and modern web-based frontend for querying a PostgreSQL database using natural language. The key frontend features include:

- User Authentication Form: A clean and secure login interface for initializing SSH and database connections using NetID, SSH password, and database password.

- Natural Language Query Input: After authentication, users can enter natural language questions about the database schema. These questions are translated into SQL queries by the LLM backend.

- Dynamic Output Display: The output screen presents:

   - The original question from the user,

   - The generated SQL query,

   - The raw LLM output.

   - Interactive Table: Query results are rendered as a responsive HTML table that supports column sorting on click, offering a better data exploration experience.

   - Modern UI Styling: Styled with a custom CSS (styles.css) for a clean, intuitive, and modern look, enhancing user interaction and readability.

Responsive Feedback and Error Handling: User feedback is clearly communicated through dynamic success/error messages and loading states to guide user interaction.

