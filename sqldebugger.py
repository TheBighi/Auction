import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect("auctions.db")
cursor = conn.cursor()

# Fetch all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Print all rows with column headers
for table in tables:
    table_name = table[0]
    print(f"\nTable: {table_name}")

    # Fetch column names
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [col[1] for col in cursor.fetchall()]  # Extract column names
    print(", ".join(columns))  # Print column headers

    # Fetch all rows from the table
    cursor.execute(f"SELECT * FROM {table_name};")
    rows = cursor.fetchall()

    # Print rows with column values
    for row in rows:
        print(", ".join(map(str, row)))  # Convert values to strings and print

# Close the connection
conn.close()

