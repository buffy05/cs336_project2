import sys
import os
import getpass
import re
import paramiko
from llama_cpp import Llama

# Model and connection details
# Ensure MODEL_PATH points to your downloaded model file.
MODEL_PATH = "Phi-3.5-mini-instruct-Q4_K_M.gguf"
SCHEMA_FILE = "schema.sql"
ILAB_HOST = "ilab.cs.rutgers.edu" # Or ilab1, ilab2, ilab3
REMOTE_SCRIPT_PATH = "~/ilab_script.py" # Path to the script on the ILAB server

# LLM Parameters
N_CTX = 2048  # Model context window size
MAX_TOKENS = 150 # Max tokens for LLM to generate
N_GPU_LAYERS = -1 # Offload layers to GPU (-1 = try all)

def load_schema(filepath):
    """Loads the SQL schema from the specified file."""
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Schema file not found at {filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading schema file: {e}", file=sys.stderr)
        sys.exit(1)

def create_prompt(schema, question):
    """Builds the prompt for the LLM using the schema and user question."""
    # Instruct the LLM to use exact schema names and output only SQL.
    prompt = f"""Given the following PostgreSQL database schema:

```sql
{schema}
```

Translate the following user question into a single, valid PostgreSQL SELECT query. **Use only the exact table and column names provided in the schema.** Only output the SQL query.

User Question: {question}
"""
    return prompt

def extract_sql(llm_output):
    """Extracts the first SQL SELECT query from the LLM's text output."""
    # print(f"\nLLM Raw Output Before Extraction Attempt:\n>>>\n{llm_output}\n<<<", file=sys.stderr) # Keep this debug line commented unless needed

    # Attempt to find SQL block using regex patterns
    # Pattern 1: ```sql\n(SELECT...)\n```
    match = re.search(r"```sql\n(SELECT.*?)\n```", llm_output, re.IGNORECASE | re.DOTALL)
    if not match:
        # Pattern 2: SQL:\s*(SELECT...)(?:;|$|\n```)
        match = re.search(r"SQL:\s*(SELECT.*?)(?:;|$|\n```)", llm_output, re.IGNORECASE | re.DOTALL)
    if not match:
        # Pattern 3: Fallback - any SELECT statement ending with ; or end of string
         match = re.search(r"(SELECT\s+.*?)(?:;|$)", llm_output, re.IGNORECASE | re.DOTALL)

    if match:
        sql_query = match.group(1).strip()
        # Clean up potential lingering markdown
        sql_query = sql_query.replace("```", "").strip()
        # Ensure it ends with a semicolon
        if not sql_query.endswith(';'):
            sql_query += ';'
        # Final check
        if sql_query.upper().startswith("SELECT"):
            # print(f"Extracted SQL: {sql_query}", file=sys.stderr) # Keep commented unless debugging
            return sql_query
        else:
             print(f"Warning: Extracted text doesn't start with SELECT: {sql_query}", file=sys.stderr)
             return None # Return None if extraction seems incorrect

    print("Warning: Could not extract SQL query from LLM response.", file=sys.stderr)
    return None


def run_remote_query(ssh_client, netid, sql_query, db_password):
    """Runs ilab_script.py remotely, passing query and password via stdin (Extra Credit method)."""
    # Extra Credit: Command now only includes netid
    command = f'python3 {REMOTE_SCRIPT_PATH} {netid}'

    # print(f"\nExecuting on {ILAB_HOST} (Extra Credit Mode): {command}", file=sys.stderr) # Keep commented
    # print(f"Sending SQL via stdin: {sql_query}", file=sys.stderr) # Keep commented

    try:
        stdin, stdout, stderr = ssh_client.exec_command(command, timeout=60)

        # Send SQL Query first, then DB password via stdin
        stdin.write(sql_query + '\n')
        stdin.write(db_password + '\n')
        stdin.flush()
        stdin.channel.shutdown_write() # Indicate end of input

        output = stdout.read().decode('utf-8', errors='ignore').strip()
        error_output = stderr.read().decode('utf-8', errors='ignore').strip()

        # Basic check for authentication errors
        if "password authentication failed" in error_output.lower():
            print("\nPostgreSQL authentication failed on ILAB. Check DB password.", file=sys.stderr)

        return output, error_output

    except Exception as e:
        print(f"Error during SSH command execution: {e}", file=sys.stderr)
        return None, str(e)


def main():
    schema = load_schema(SCHEMA_FILE)

    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model file not found at {MODEL_PATH}", file=sys.stderr)
        print("Please download the model or update MODEL_PATH.", file=sys.stderr) # Slightly simpler message
        sys.exit(1)

    print(f"Loading model from {MODEL_PATH}...")
    try:
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=N_CTX,
            n_threads=None, # Use llama.cpp default
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False # Keep this off for cleaner output
        )
        print("Model loaded.") # Shorter success message
    except Exception as e:
        # Fallback to CPU if GPU fails
        print(f"Warning: GPU load failed ({e}). Trying CPU only.", file=sys.stderr) # Slightly simpler warning
        try:
            llm = Llama(
                model_path=MODEL_PATH,
                n_ctx=N_CTX,
                n_threads=None,
                n_gpu_layers=0, # Force CPU
                verbose=False
            )
            print("Model loaded (CPU only).") # Shorter
        except Exception as e2:
            print(f"Fatal: Error loading LLM on CPU: {e2}", file=sys.stderr) # Clearer error
            sys.exit(1)

    # Get ILAB credentials securely
    ilab_netid = input("Enter ILAB NetID: ").strip()
    ilab_ssh_password = getpass.getpass("Enter ILAB SSH password: ")
    ilab_db_password = getpass.getpass("Enter ILAB PostgreSQL password: ")

    # Initialize SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Auto-accept host key (standard practice)

    try:
        print(f"Connecting to {ILAB_HOST}...") # Simpler message
        ssh.connect(ILAB_HOST, username=ilab_netid, password=ilab_ssh_password, look_for_keys=False, allow_agent=False, timeout=30)
        print("SSH connection established.")

        # Main interaction loop
        while True:
            try:
                question = input("\nEnter question (or 'exit'): ") # Shorter prompt
                if question.lower() == 'exit':
                    break
                if not question:
                    continue

                prompt = create_prompt(schema, question)

                print("\nGenerating SQL...", file=sys.stderr) # Shorter message
                try:
                    # Generate response from LLM
                    response = llm(prompt, max_tokens=MAX_TOKENS, stop=[";"], echo=False)
                    # print(f"DEBUG: Full LLM Response object:\n{response}", file=sys.stderr) # Keep commented
                    llm_output = response['choices'][0]['text'].strip()
                except Exception as e:
                    print(f"Error during LLM generation: {e}", file=sys.stderr)
                    continue # Ask for next question

                sql_query = extract_sql(llm_output)

                if sql_query:
                    # Execute query remotely via SSH
                    db_results, db_errors = run_remote_query(ssh, ilab_netid, sql_query, ilab_db_password)

                    print("\n--- Database Results ---")
                    if db_results:
                        print(db_results)
                    else:
                        # Check if errors indicate success without output (e.g. for non-SELECT)
                        if db_errors and "Query executed successfully" in db_errors:
                             print("(Query executed successfully, no results to display)")
                        elif not db_errors:
                             print("(No results returned or query produced no output)")


                    # Process and display errors from the remote script
                    if db_errors:
                        filtered_errors = "\n".join(line for line in db_errors.splitlines()
                                                  if "Executing Query:" not in line and \
                                                     "Reading password from stdin..." not in line and \
                                                     "Query executed successfully" not in line)
                        if filtered_errors:
                            print("\n--- Errors/Messages from ILAB Script ---", file=sys.stderr)
                            print(filtered_errors, file=sys.stderr)
                        # Highlight specific critical errors
                        if "password authentication failed" in db_errors.lower():
                             print("\n** PostgreSQL authentication failed on ILAB. Check DB password. **", file=sys.stderr)
                        elif "psycopg2.errors" in db_errors:
                             print("\n** SQL Error reported by ILAB script. **", file=sys.stderr)

                else:
                    print("\nFailed to generate a valid SQL query.") # Simpler message
                    # print(f"LLM Response was: {llm_output}") # Option to show user the raw response if extraction fails


            except EOFError: # Handle Ctrl+D
                 print("\nExiting...")
                 break
            except KeyboardInterrupt: # Handle Ctrl+C
                 print("\nExiting...")
                 break

    except paramiko.AuthenticationException:
        print("\nSSH Authentication failed. Check NetID and SSH password.", file=sys.stderr) # Simpler message
    except paramiko.SSHException as sshException:
        print(f"\nSSH connection failed: {sshException}", file=sys.stderr) # Simpler message
    except Exception as e:
        print(f"\nAn unexpected error occurred in main loop: {e}", file=sys.stderr) # More specific
    finally:
        # Cleanly close SSH connection
        if ssh.get_transport() and ssh.get_transport().is_active():
            print("\nClosing SSH connection.", file=sys.stderr)
            ssh.close()

    print("\nProgram finished.")


if __name__ == "__main__":
    main()
