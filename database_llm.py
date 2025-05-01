import sys
import os
import getpass
import re
import paramiko
from llama_cpp import Llama

# --- Configuration ---
# !!! IMPORTANT INFO GUYS: Replace with the actual path to your downloaded model if it's not in the same directory !!!
MODEL_PATH = "Phi-3.5-mini-instruct-Q4_K_M.gguf"
SCHEMA_FILE = "schema.sql"
ILAB_HOST = "ilab.cs.rutgers.edu" # Or ilab1, ilab2, ilab3
REMOTE_SCRIPT_PATH = "~/ilab_script.py" # Assumes ilab_script.py is in the home directory on ILAB

# LLM Parameters (adjust as needed)
N_CTX = 2048  # Context window size
MAX_TOKENS = 150 # Max tokens to generate
N_GPU_LAYERS = -1 # -1 means attempt to offload all layers to GPU (Metal on Mac)

# --- Function to Load Schema ---
def load_schema(filepath):
    """Loads the SQL schema from a file."""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Schema file not found at {filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading schema file: {e}", file=sys.stderr)
        sys.exit(1)

# --- Function to Create LLM Prompt ---
def create_prompt(schema, question):
    """Creates the prompt for the LLM, encouraging SQL output."""
    # Added explicit instruction to use exact names from schema
    prompt = f"""Given the following PostgreSQL database schema:

```sql
{schema}
```

Translate the following user question into a single, valid PostgreSQL SELECT query. **Use only the exact table and column names provided in the schema.** Only output the SQL query.

User Question: {question}
"""
    return prompt

# --- Function to Extract SQL Query ---
def extract_sql(llm_output):
    """Extracts the first SQL query block from the LLM output."""
    # Basic regex: find text between "SQL:" and potential markdown/end of string
    # It looks for SELECT and assumes the query ends with a semicolon or the end of the string.
    # This might need significant refinement based on actual LLM output.
    print(f"\nLLM Raw Output Before Extraction Attempt:\n>>>\n{llm_output}\n<<<", file=sys.stderr) # Debugging - Show raw output

    # Try to find SQL block, possibly after "SQL:" or within ```sql ... ```
    # Pattern 1: Explicit SQL block
    match = re.search(r"```sql\n(SELECT.*?)\n```", llm_output, re.IGNORECASE | re.DOTALL)
    if not match:
        # Pattern 2: After "SQL:" prompt hint
        match = re.search(r"SQL:\s*(SELECT.*?)(?:;|$|\n```)", llm_output, re.IGNORECASE | re.DOTALL)
    if not match:
        # Pattern 3: Fallback - any SELECT statement
         match = re.search(r"(SELECT\s+.*?)(?:;|$)", llm_output, re.IGNORECASE | re.DOTALL)


    if match:
        sql_query = match.group(1).strip()
        # Remove potential trailing markdown backticks if pattern 2/3 matched them
        sql_query = sql_query.replace("```", "").strip()
        # Ensure it ends with a semicolon for consistency
        if not sql_query.endswith(';'):
            sql_query += ';'
        # Basic validation: ensure it starts with SELECT
        if sql_query.upper().startswith("SELECT"):
            print(f"Extracted SQL: {sql_query}", file=sys.stderr) # Debugging
            return sql_query
        else:
             print(f"Warning: Extracted text doesn't start with SELECT: {sql_query}", file=sys.stderr)
             return None

    print("Warning: Could not extract SQL query from LLM response.", file=sys.stderr)
    return None


# --- Function to Run Remote Script ---
def run_remote_query(ssh_client, netid, sql_query, db_password):
    """Executes the ilab_script.py remotely via SSH, passing DB password via stdin."""
    # Ensure the SQL query is properly quoted for the command line
    escaped_sql = sql_query.replace('"', '\\"') # escape double quotes
    command = f'python3 {REMOTE_SCRIPT_PATH} {netid} "{escaped_sql}"'

    print(f"\nExecuting on {ILAB_HOST}: {command}", file=sys.stderr)

    try:
        # Execute the command
        stdin, stdout, stderr = ssh_client.exec_command(command, timeout=60)

        # Send the DB password to the remote script's stdin
        stdin.write(db_password + '\n')
        stdin.flush()
        stdin.channel.shutdown_write() # Signal that we are done writing to stdin

        # Read the output (database results)
        output = stdout.read().decode('utf-8', errors='ignore').strip()
        # Read any errors or debug info
        error_output = stderr.read().decode('utf-8', errors='ignore').strip()

        # Check for explicit password failure in stderr, just in case
        if "password authentication failed" in error_output.lower():
            print("\nPostgreSQL authentication failed on ILAB. Check DB password.", file=sys.stderr)

        return output, error_output

    except Exception as e:
        print(f"Error during SSH command execution: {e}", file=sys.stderr)
        return None, str(e)


# --- Main Function ---
def main():
    # --- Load Schema ---
    schema = load_schema(SCHEMA_FILE)

    # --- Initialize LLM ---
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model file not found at {MODEL_PATH}", file=sys.stderr)
        print("Please download the model and place it correctly, or update MODEL_PATH.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading model from {MODEL_PATH}... (This may take a moment)")
    try:
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=N_CTX,          # Context window
            n_threads=None,       # Use default number of threads
            n_gpu_layers=N_GPU_LAYERS, # Offload layers to GPU
            verbose=False         # Set back to False
        )
        print("Model loaded successfully.")
    except Exception as e:
        # Try loading without GPU offloading as a fallback
        print(f"Warning: Error loading LLM with GPU layers ({e}). Trying CPU only.", file=sys.stderr)
        try:
            llm = Llama(
                model_path=MODEL_PATH,
                n_ctx=N_CTX,
                n_threads=None,
                n_gpu_layers=0, # Force CPU
                verbose=False # Set back to False
            )
            print("Model loaded successfully (CPU only).")
        except Exception as e2:
            print(f"Error loading LLM on CPU either: {e2}", file=sys.stderr)
            sys.exit(1)


    # --- Get Credentials ---
    ilab_netid = input("Enter your ILAB NetID: ").strip()
    ilab_ssh_password = getpass.getpass("Enter your ILAB SSH password: ")
    ilab_db_password = getpass.getpass("Enter your ILAB PostgreSQL password: ")

    # --- Initialize SSH Client ---
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Auto-accept host key

    try:
        print(f"Connecting to {ilab_netid}@{ILAB_HOST}...", file=sys.stderr)
        ssh.connect(ILAB_HOST, username=ilab_netid, password=ilab_ssh_password, look_for_keys=False, allow_agent=False, timeout=30)
        print("SSH connection established.", file=sys.stderr)

        # --- Interaction Loop ---
        while True:
            try:
                question = input("\nEnter your question (or type 'exit' to quit): ")
                if question.lower() == 'exit':
                    break
                if not question:
                    continue

                # --- Generate Prompt ---
                prompt = create_prompt(schema, question)

                # --- Get LLM Response ---
                print("\nGenerating SQL query...", file=sys.stderr)
                try:
                    response = llm(prompt, max_tokens=MAX_TOKENS, stop=[";"], echo=False)
                    print(f"DEBUG: Full LLM Response object:\n{response}", file=sys.stderr)
                    llm_output = response['choices'][0]['text'].strip()
                except Exception as e:
                    print(f"Error during LLM generation: {e}", file=sys.stderr)
                    continue # Ask for next question

                # --- Extract SQL ---
                sql_query = extract_sql(llm_output)

                if sql_query:
                    # --- Execute Remotely ---
                    db_results, db_errors = run_remote_query(ssh, ilab_netid, sql_query, ilab_db_password)

                    print("--- Database Results ---")
                    if db_results:
                        print(db_results)
                    else:
                        print("(No results returned)")

                    if db_errors:
                        # Don't print the password prompt as an error (it shouldn't appear now)
                        filtered_errors = "\n".join(line for line in db_errors.splitlines() if "Enter PostgreSQL password" not in line)
                        if filtered_errors:
                            print("--- Errors/Messages from ILAB Script ---", file=sys.stderr)
                            print(filtered_errors, file=sys.stderr)
                        # Check for actual authentication failure
                        if "password authentication failed" in db_errors.lower():
                             print("\nPostgreSQL authentication failed on ILAB. Check DB password.", file=sys.stderr)
                        elif "psycopg2.errors" in db_errors: # Check for SQL execution errors
                             print("\nSQL Error reported by ILAB script.", file=sys.stderr)


                else:
                    print("\nFailed to generate a valid SQL query for your question.")
                    print(f"LLM Response was: {llm_output}") # Show user what LLM produced


            except EOFError: # Handle Ctrl+D
                 break
            except KeyboardInterrupt: # Handle Ctrl+C
                 print("\nExiting...")
                 break

    except paramiko.AuthenticationException:
        print("\nSSH Authentication failed. Please check your NetID and SSH password.", file=sys.stderr)
    except paramiko.SSHException as sshException:
        print(f"\nCould not establish SSH connection: {sshException}", file=sys.stderr)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
    finally:
        # --- Close SSH Connection ---
        if ssh.get_transport() and ssh.get_transport().is_active():
            print("\nClosing SSH connection.", file=sys.stderr)
            ssh.close()

    print("\nProgram finished.")


if __name__ == "__main__":
    main()
