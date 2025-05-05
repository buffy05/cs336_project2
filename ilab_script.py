import sys
import psycopg2
import pandas as pd

#function to execute the query on the ILAB database (querytaker takes in netid so as not to keep retyping netid)
def querytaker(query, netid):
    #print(f"Executing Query: {query}", file=sys.stderr)

    db_host = "postgres.cs.rutgers.edu"
    db_name = netid
    db_username = netid
    db_password = None

    try:
        #read db password from standard input
        #print("Reading password from stdin", file=sys.stderr)
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
            #printing df to stdout for the local script
            print(df.to_string(index=False))
        else:
            #if succesful but nothing to show (for fringe select cases if needed (probably not))
            print("Query executed successfully, no results to display.", file=sys.stderr)

    #error reporting and showing any exceptions (also closing the connection as per llm guidance) 
    except psycopg2.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'curr' in locals() and curr:
            curr.close()
        if 'conn' in locals() and conn:
            conn.close()


def main():
    netid = None
    query = None

    #does both standard and extra credit input styles
    #reading query from stdin
    if len(sys.argv) == 2:
        netid = sys.argv[1]
        #print("Reading SQL query from stdin.", file=sys.stderr)
        query = sys.stdin.readline().rstrip()
        if not query:
             print("Error: No query received via stdin.", file=sys.stderr)
             sys.exit(1)
    #if reading query from regular argument (not extra credit, tested first) 
    elif len(sys.argv) == 3:
        netid = sys.argv[1]
        query = sys.argv[2]
    #another fringe case, combined cases, probably not necessary but just in case
    else:
        print("Usage (Stdin Query): python3 ilab_script.py <netid>", file=sys.stderr)
        print("Usage (Arg Query):   python3 ilab_script.py <netid> \"<SQL Query>\"", file=sys.stderr)
        print(f"Received {len(sys.argv)} arguments: {sys.argv}", file=sys.stderr)
        sys.exit(1)

    #must be select querey, checking here to make sure it is (but did account for it in querytaker fringe cases)
    if not query.strip().upper().startswith("SELECT"):
        print(f"Error: Query must start with SELECT. Received: {query[:100]}...", file=sys.stderr)
        sys.exit(1)

    #executing querey 
    querytaker(query, netid)

if __name__ == "__main__":
    main()
