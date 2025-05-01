import sys
import psycopg2
import pandas as pd
import getpass

# Function to execute the query on the ILAB database
def querytaker(query, netid):
    start_check = query.strip().upper().startswith("SELECT")
    if not start_check:
        print(f"Error: Query must start with SELECT.", file=sys.stderr)
        sys.exit(1) # Exit if query is invalid

    # For debugging purposes on the remote server
    print(f"Executing Query: {query}", file=sys.stderr) # Print debug info to stderr

    db_host = "postgres.cs.rutgers.edu"
    db_name = netid
    db_username = netid
    db_password = None # Initialize password

    try:
        # Read password from standard input
        print("Reading password from stdin...", file=sys.stderr) # Debug message
        db_password = sys.stdin.readline().rstrip()
        if not db_password:
            print("Error: No password received via stdin.", file=sys.stderr)
            sys.exit(1)

        # print(f"DEBUG: Received password of length {len(db_password)}", file=sys.stderr) # Uncomment for deep debug

        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_username,
            password=db_password
        )
        curr = conn.cursor()
        curr.execute(query)

        # Check if the query returns results (e.g., SELECT)
        if curr.description:
            rows = curr.fetchall()
            col_names = [desc[0] for desc in curr.description]
            df = pd.DataFrame(rows, columns=col_names)
            # Print DataFrame to stdout for the local script to capture
            print(df.to_string(index=False))
        else:
            # Handle non-SELECT queries or queries with no output (e.g., successful INSERT/UPDATE)
            print("Query executed successfully, no results to display.", file=sys.stderr)


    except psycopg2.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1) # Exit on database errors

    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1) # Exit on other errors

    finally:
        # Ensure cleanup happens
        if 'curr' in locals() and curr:
            curr.close()
        if 'conn' in locals() and conn:
            conn.close()


def main():
    # Expecting 3 arguments: script_name, netid, query
    if len(sys.argv) != 3:
        print("Usage: python3 ilab_script.py <netid> \"<SQL Query>\"", file=sys.stderr)
        print(f"Received {len(sys.argv)} arguments: {sys.argv}", file=sys.stderr)
        sys.exit(1)

    netid = sys.argv[1]
    query = sys.argv[2] # Query is the second argument

    # Call the query execution function
    querytaker(query, netid)

if __name__ == "__main__":
    main()