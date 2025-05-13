from flask import Flask, render_template, request, jsonify
import sys
import os
import getpass
import re
import paramiko
from llama_cpp import Llama
import pandas as pd
from io import StringIO

app = Flask(__name__)

# Model and connection details (same as database_llm.py)
MODEL_PATH = "Phi-3.5-mini-instruct-Q4_K_M.gguf"
SCHEMA_FILE = "schema.sql"
ILAB_HOST = "ilab.cs.rutgers.edu"
REMOTE_SCRIPT_PATH = "~/ilab_script.py"

# LLM Parameters
N_CTX = 2048
MAX_TOKENS = 150
N_GPU_LAYERS = -1

# Global variables for persistent connections
llm = None
ssh_client = None
schema = None

def initialize_llm():
    global llm
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
    
    try:
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=N_CTX,
            n_threads=None,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False
        )
    except Exception as e:
        try:
            llm = Llama(
                model_path=MODEL_PATH,
                n_ctx=N_CTX,
                n_threads=None,
                n_gpu_layers=0,
                verbose=False
            )
        except Exception as e2:
            raise Exception(f"Failed to load LLM: {e2}")

def load_schema():
    global schema
    try:
        with open(SCHEMA_FILE, 'r') as f:
            schema = f.read()
    except Exception as e:
        raise Exception(f"Error reading schema file: {e}")

def create_prompt(question):
    prompt = f"""Given the following PostgreSQL database schema:

```sql
{schema}
```

Translate the following user question into a single, valid PostgreSQL SELECT query. **Use only the exact table and column names provided in the schema.** Only output the SQL query.

User Question: {question}
"""
    return prompt

def extract_sql(llm_output):
    match = re.search(r"```sql\n(SELECT.*?)\n```", llm_output, re.IGNORECASE | re.DOTALL)
    if not match:
        match = re.search(r"SQL:\s*(SELECT.*?)(?:;|$|\n```)", llm_output, re.IGNORECASE | re.DOTALL)
    if not match:
        match = re.search(r"(SELECT\s+.*?)(?:;|$)", llm_output, re.IGNORECASE | re.DOTALL)

    if match:
        sql_query = match.group(1).strip()
        sql_query = sql_query.replace("```", "").strip()
        if not sql_query.endswith(';'):
            sql_query += ';'
        if sql_query.upper().startswith("SELECT"):
            return sql_query
    return None

def normalize_results(results_str):
    """Convert pandas DataFrame string output to list of dictionaries"""
    if not results_str or results_str.strip() == "":
        return []
    
    try:
        # Read the string into a pandas DataFrame
        df = pd.read_csv(StringIO(results_str), sep=r'\s+')
        # Convert to list of dictionaries
        return df.to_dict('records')
    except Exception as e:
        print(f"Error normalizing results: {e}", file=sys.stderr)
        return []

def run_remote_query(sql_query, netid, db_password):
    global ssh_client
    
    if not ssh_client or not ssh_client.get_transport() or not ssh_client.get_transport().is_active():
        raise Exception("SSH connection not active")
    
    command = f'python3 {REMOTE_SCRIPT_PATH} {netid}'
    
    try:
        stdin, stdout, stderr = ssh_client.exec_command(command, timeout=60)
        stdin.write(sql_query + '\n')
        stdin.write(db_password + '\n')
        stdin.flush()
        stdin.channel.shutdown_write()
        
        output = stdout.read().decode('utf-8', errors='ignore').strip()
        error_output = stderr.read().decode('utf-8', errors='ignore').strip()
        
        if "password authentication failed" in error_output.lower():
            raise Exception("PostgreSQL authentication failed")
            
        return output, error_output
    except Exception as e:
        raise Exception(f"Error during SSH execution: {e}")

@app.route('/initialize', methods=['POST'])
def initialize():
    try:
        global llm, ssh_client, schema
        
        # Get credentials from request
        data = request.get_json()
        if not data or 'netid' not in data or 'ssh_password' not in data or 'db_password' not in data:
            return jsonify({'error': 'Missing credentials'}), 400
            
        netid = data['netid']
        ssh_password = data['ssh_password']
        db_password = data['db_password']
        
        # Initialize LLM if not already done
        if llm is None:
            initialize_llm()
            
        # Load schema if not already done
        if schema is None:
            load_schema()
            
        # Initialize SSH connection
        if ssh_client is None or not ssh_client.get_transport() or not ssh_client.get_transport().is_active():
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(ILAB_HOST, username=netid, password=ssh_password, 
                             look_for_keys=False, allow_agent=False, timeout=30)
        
        return jsonify({'status': 'success', 'message': 'Initialization successful'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/query', methods=['POST'])
def process_query():
    try:
        if llm is None or schema is None or ssh_client is None:
            return jsonify({'error': 'System not initialized'}), 400
            
        data = request.get_json()
        if not data or 'question' not in data or 'netid' not in data or 'db_password' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
            
        question = data['question']
        netid = data['netid']
        db_password = data['db_password']
        
        # Generate SQL query
        prompt = create_prompt(question)
        response = llm(prompt, max_tokens=MAX_TOKENS, stop=[";"], echo=False)
        llm_output = response['choices'][0]['text'].strip()
        
        sql_query = extract_sql(llm_output)
        if not sql_query:
            return jsonify({'error': 'Failed to generate valid SQL query'}), 400
            
        # Execute query
        results_str, error_output = run_remote_query(sql_query, netid, db_password)
        
        # Normalize results
        results = normalize_results(results_str)
        
        return jsonify({
            'status': 'success',
            'sql_query': sql_query,
            'llm_output': llm_output,
            'results': results,
            'error': error_output if error_output else None
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
