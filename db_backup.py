import sqlite3
import shutil

# Source database file
source_db_file = 'instance\pdfdrive.db'

# Copied database file
copied_db_file = 'copied.db'

# Copy the source database file to create a new copy
shutil.copyfile(source_db_file, copied_db_file)

# Connect to the source database
source_conn = sqlite3.connect(source_db_file)

# Connect to the copied database
copied_conn = sqlite3.connect(copied_db_file)

# Create a cursor for both connections
source_cursor = source_conn.cursor()
copied_cursor = copied_conn.cursor()

# Attach the copied database to the new connection
copied_cursor.execute(f"ATTACH DATABASE '{copied_db_file}' AS copied")

# Export the entire data from the source to the copied database
copied_cursor.execute("BEGIN")
for table_name in source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';"):
    table_name = table_name[0]
    if table_name != 'category':
        query = f"INSERT INTO copied.{table_name} SELECT * FROM {table_name};"
    else:
        query = f"INSERT INTO copied.{table_name} SELECT id, category_name FROM {table_name};"
    copied_cursor.execute(query)

# Commit the changes and close the connections
copied_cursor.execute("COMMIT")
source_conn.close()
copied_conn.close()

print("Database copied successfully.")
