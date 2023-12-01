# from datetime import datetime

# from cat.mad_hatter.decorators import tool, hook
# import logging
# import sqlite3
# from cat.log import log

# @hook
# def before_cat_bootstrap(cat) -> None:
#     import sqlite3

#     # Connect to SQLite database (it will be created if it doesn't exist)
#     conn = sqlite3.connect('sample.db')

#     # Create a cursor object to execute SQL queries
#     cursor = conn.cursor()

#     # Create a 'users' table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS users (
#             id INTEGER PRIMARY KEY,
#             name TEXT,
#             age INTEGER
#         )
#     ''')

#     # Insert some sample data into the 'users' table
#     cursor.execute("INSERT INTO users (name, age) VALUES (?, ?)", ('John Doe', 30))
#     cursor.execute("INSERT INTO users (name, age) VALUES (?, ?)", ('Jane Doe', 25))
#     cursor.execute("INSERT INTO users (name, age) VALUES (?, ?)", ('Bob Smith', 40))

#     # Create an 'orders' table
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS orders (
#             id INTEGER PRIMARY KEY,
#             user_id INTEGER,
#             product TEXT,
#             quantity INTEGER,
#             FOREIGN KEY (user_id) REFERENCES users (id)
#         )
#     ''')

#     # Insert some sample data into the 'orders' table
#     cursor.execute("INSERT INTO orders (user_id, product, quantity) VALUES (?, ?, ?)", (1, 'Product A', 2))
#     cursor.execute("INSERT INTO orders (user_id, product, quantity) VALUES (?, ?, ?)", (2, 'Product B', 1))
#     cursor.execute("INSERT INTO orders (user_id, product, quantity) VALUES (?, ?, ?)", (3, 'Product C', 3))

#     # Commit the changes and close the connection
#     conn.commit()
#     conn.close()



# @hook
# def agent_prompt_prefix(prefix, cat) -> str:
#     prefix = """
# You are an AI assistant which is able to access relational databases to answer questions.\n\n
#     """
    
#     return prefix

# def get_database_info(db_file):

#     # Connect to SQLite database
#     conn = sqlite3.connect(db_file)

#     # Create a cursor object to execute SQL queries
#     cursor = conn.cursor()

#     # Dictionary to store tables, columns, and types
#     database_info = {}

#     # 1) Get all tables
#     cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
#     tables = cursor.fetchall()
#     tables = [table[0] for table in tables]

#     for table in tables:
#         # 2) Get all table columns and types
#         cursor.execute(f"PRAGMA table_info({table})")
#         columns_info = cursor.fetchall()
#         columns = {column[1]: column[2] for column in columns_info}

#         # Store information in the dictionary
#         database_info[table] = columns

#     # Close the connection
#     conn.close()

#     return database_info

# def print_database_info(database_info):
#     # Print the information in a human-readable form
#     pretty_print = ""
#     for table, columns in database_info.items():
#         pretty_print += f"Table: {table}\n"
#         pretty_print += f"  Columns:\n"
#         for column, data_type in columns.items():
#             pretty_print += f"  - Column: {column}, Type: {data_type}"
#         pretty_print += "\n"
#     return pretty_print


# @hook
# def before_cat_reads_message(user_message_json: dict, cat) -> dict:

#     database_info = get_database_info('sample.db')


#     import sqlite3
#     log.info(f"Calling OPENAI API")
#     import requests
#     import json
#     url = "https://api.openai.com/v1/chat/completions"
#     payload = {
#         "model": "gpt-3.5-turbo",
#         "messages": [
#             {
#                 "role": "user",
#                 "content": f"""
#                     You are a knowledge explorer assistant.
#                     Given some table and column information:
#                     1) Find the tables related to user questions
#                     2) Find the columns related to user questions
#                     3) Answer with a json array. Each element of the array is a dict containing a query to get relevant information from the database, and a description of the result.

#                     {{"queries": [ {{"query":"SELECT age FROM users WHERE name = 'John Doe'","description":"Age of John Doe:"}},{{"query":"SELECT * FROM orders WHERE user_id = 1","description":"All orders of user with id 1:"}} ]}}

#                     ## User Request

#                     ### Database Information
#                     {print_database_info(database_info)}

#                     ### Question
#                     {user_message_json["text"]}

#                     ### Answer
#                 """.strip()
#             }
#         ]
#     }

#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": "Bearer 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"
#     }
#     response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
#     print(response.text)

#     response = response.json()
#     # write to file
#     with open("response.json", "w") as outfile:
#         json.dump(response, outfile)
#     queries = json.loads(response["choices"][0]["message"]["content"])
#     log.info(queries)

#     # Execute the queries
#     # Connect to SQLite database
#     conn = sqlite3.connect('sample.db')

#     # Create a cursor object to execute SQL queries
#     db_augmented_context = ""
#     cursor = conn.cursor()
#     for query in queries["queries"]:
#         log.info(f"Executing query: {query}")
#         cursor.execute(query["query"])
#         results = cursor.fetchone()
#         print("RESULTS")
#         print(results)
#         db_augmented_context += f"""
#             {query["description"]} {results}
#         """     

#     user_message_json["text"] = f"""
#         ### Database Retrieved Data
#         {db_augmented_context}

#         ### User Request
#         {user_message_json["text"]}
#     """.strip()

#     return user_message_json