import sys
import psycopg2
import pandas as pd

# Function to execute the query on the ILAB database
def querytaker(query, netid):
    # For debugging purposes on the remote server
    # print(f"Executing Query: {query}", file=sys.stderr) # Keep commented unless debugging

    db_host = "postgres.cs.rutgers.edu"
    db_name = netid
    db_username = netid
    db_password = None

    try:
        # Read DB password from standard input
        # print("Reading password from stdin...", file=sys.stderr) # Keep commented unless debugging
        db_password = sys.stdin.readline().rstrip()
        if not db_password:
            print("Error: No password received via stdin.", file=sys.stderr)
            sys.exit(1)

        conn = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_username,
            password=db_password
        )
        curr = conn.cursor()
        curr.execute(query)

        if curr.description:
            rows = curr.fetchall()
            col_names = [desc[0] for desc in curr.description]
            df = pd.DataFrame(rows, columns=col_names)
            # Print DataFrame to stdout for the local script
            print(df.to_string(index=False))
        else:
            # Indicate successful execution for non-SELECT queries
            print("Query executed successfully, no results to display.", file=sys.stderr)

    except psycopg2.Error as e:
        # Report database errors clearly
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Report other unexpected errors
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Ensure database connection is closed
        if 'curr' in locals() and curr:
            curr.close()
        if 'conn' in locals() and conn:
            conn.close()


def main():
    netid = None
    query = None

    # Handle standard vs extra credit invocation
    if len(sys.argv) == 2: # Extra Credit: Read query from stdin
        netid = sys.argv[1]
        # print("Reading SQL query from stdin...", file=sys.stderr) # Keep commented unless debugging
        query = sys.stdin.readline().rstrip()
        if not query:
             print("Error: No query received via stdin.", file=sys.stderr)
             sys.exit(1)

    elif len(sys.argv) == 3: # Standard (for potential manual testing): Read query from arg
        netid = sys.argv[1]
        query = sys.argv[2]
    else:
        # Print usage message for both modes
        print("Usage (Stdin Query): python3 ilab_script.py <netid>", file=sys.stderr)
        print("Usage (Arg Query):   python3 ilab_script.py <netid> \"<SQL Query>\"", file=sys.stderr)
        print(f"Received {len(sys.argv)} arguments: {sys.argv}", file=sys.stderr)
        sys.exit(1)

    # Validate the query (must be SELECT)
    if not query.strip().upper().startswith("SELECT"):
        print(f"Error: Query must start with SELECT. Received: {query[:100]}...", file=sys.stderr)
        sys.exit(1)

    # Execute the query
    querytaker(query, netid)

if __name__ == "__main__":
    main()