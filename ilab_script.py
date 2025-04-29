import sys
import psycopg2
import pandas as pd
import getpass

#made db_password in main instead of here so you don't have to keep entering password everytime you enter query during session
def querytaker(query, netid, db_password): 
    start_check = query.startswith("SELECT")
    if not start_check:
        print(f"query not formatted correctly")
        return
    #for debugging purposes
    print(f"query: {query}")
    db_host = "postgres.cs.rutgers.edu"
    db_name = netid
    db_username = netid
    #db_password = getpass.getpass("Enter postgresql password: ")
    
    try: 
        conn = psycopg2.connect(
            host = db_host, 
            database = db_name, 
            user = db_username, 
            password = db_password
            )
    
        curr = conn.cursor()
        curr.execute(query)
        rows = curr.fetchall()
        col_names = [desc[0] for desc in curr.description]
        df = pd.DataFrame(rows, columns = col_names)
        print(df.to_string(index = False))

    #if it encounters an error, will state the error (like if a col doesnt exist), and keep going
    except psycopg2.Error as e: 
        print(f"Database error: {e}", file=sys.stderr)
        #sys.exit(1) 

    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        #sys.exit(1)

    finally: 
        if curr: 
            curr.close()
        if conn: 
            conn.close()


def main(): 
    #if no argument given, reading from stdinput
    #for extra credit point
    #get netid and password
    netid = input("Enter netid/db_credentials: ").rstrip()
    db_password = getpass.getpass("Enter postgresql (ilab) password: ")
    if len(sys.argv) == 1:
        print("Enter queries (enter q for end of input): ")
        for query in sys.stdin: 
            query = query.rstrip()
            if query == 'q':
                break #reached end of input
            querytaker(query, netid, db_password)
    else: #assuming that arguments will either be 0 (read in stdin) or 1 (single query)
    #will adjust if multiple arguments given (put in loop)
        #reading from command line argument (single query?)
        
        #assumes query is in "SELECT ... ;" format (quotes included)
        query = sys.argv[1].rstrip()
        querytaker(query, netid, db_password)



if __name__ == "__main__": 
    main()