import json

from cat.log import log
from cat.mad_hatter.decorators import hook
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List

Base = declarative_base()


class DatabaseManager:
    def __init__(self, db_uri):
        self.engine = create_engine(db_uri)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def execute_query(self, query):
        session = self.Session()
        result = session.execute(text(query)).all()
        session.commit()
        session.close()
        return result

    def get_database_info(self):
        inspector = inspect(self.engine)
        tables_info = {}

        for table_name in inspector.get_table_names():
            if "missions" in table_name:
                columns_info = {column["name"]: str(
                    column["type"]) for column in inspector.get_columns(table_name)}
                tables_info[table_name] = columns_info

        return tables_info

    def print_database_info(self, database_info):
        pretty_print = ""
        for table, columns in database_info.items():
            pretty_print += f"Table: {table}\n"
            for column, data_type in columns.items():
                # pretty_print += f"  - Column: {column}, Type: {data_type}\n"
                # Spare tokens
                pretty_print += f" {column}: {data_type}\n"
            pretty_print += "\n"
        return pretty_print


class SqliteDatabaseManager(DatabaseManager):
    class User(Base):
        __tablename__ = 'users'

        id = Column(Integer, primary_key=True)
        name = Column(String)
        age = Column(Integer)

    class Order(Base):
        __tablename__ = 'orders'

        id = Column(Integer, primary_key=True)
        user_id = Column(Integer, ForeignKey('users.id'))
        product = Column(String)
        quantity = Column(Integer)

    def __init__(self, db_uri='sqlite:///sample.db'):
        super().__init__(db_uri)

    def drop_tables(self):
        Base.metadata.drop_all(self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def insert_sample_data(self):
        session = self.Session()

        # Sample data for demonstration
        user1 = self.User(name='John Doe', age=30)
        user2 = self.User(name='Jane Doe', age=25)
        user3 = self.User(name='Bob Smith', age=40)

        order1 = self.Order(user_id=1, product='Product A', quantity=2)
        order2 = self.Order(user_id=1, product='Product A', quantity=5)
        order3 = self.Order(user_id=2, product='Product B', quantity=1)
        order4 = self.Order(user_id=3, product='Product C', quantity=3)

        session.add_all([user1, user2, user3, order1, order2, order3, order4])
        session.commit()
        session.close()


@hook
def before_cat_bootstrap(cat) -> None:
    settings = cat.mad_hatter.plugins["db_gpt"].load_settings()
    db_manager = DatabaseManager(db_uri=settings["db_uri"])
    # db_manager = SqliteDatabaseManager(db_uri=settings["db_uri"])
    # db_manager.drop_tables()
    # db_manager.create_tables()
    # db_manager.insert_sample_data()


@hook
def agent_prompt_prefix(prefix, cat) -> str:
    return """
    You are an AI assistant which is able to access relational databases to answer questions.\n\n
    """

user_message = None
cat_message = None

@hook
def before_cat_reads_message(user_message_json: dict, cat) -> dict:
    global cat_message
    global user_message
    user_message = build_message(cat, user_message_json["text"])
    cat_message = send_message_to_agent_without_memory(user_message, cat)
    log.info(f"CAT MESSAGE: {cat_message}")
    queries = get_queries_from_output(cat_message)
    db_augmented_context = process_queries(cat, queries)
    user_message_json["text"] = enrich_user_message_with_db_context(
        user_message_json, db_augmented_context
    )
    return user_message_json

# @hook
# def before_cat_sends_message(message: dict, cat) -> dict:
#     global cat_message
#     global user_message
#     log.info(f"CAT MESSAGE (in before sends message): {cat_message}")
#     queries = get_queries_from_output(cat_message)
#     queries = [query["query"] for query in queries]
#     message["content"] = f"""
#         {message["content"]}
#         ______________________________________________
#         # Input words: {len(user_message.split())}
#         # Output words: {len(message["content"].split())}
#         {"<br>".join(queries)}
#     """.strip()
#     return message



def send_message_to_agent_without_memory(user_message: str, cat):
    cat_message = cat.agent_manager.execute_agent(
        {
            "history": [],
            "episodic_memories": [],
            "declarative_memories": [],
            "procedural_memories": [],
            "user_message_json": {"text": user_message}
        }
    )
    return cat_message


def build_message(cat, user_message: str):
    settings = cat.mad_hatter.plugins["db_gpt"].load_settings()
    db_manager = DatabaseManager(db_uri=settings["db_uri"])
    return f"""
        You are a knowledge explorer assistant.
        Given some table and column information:
        1) Find the tables related to user questions
        2) Find the columns related to user questions
        3) Answer with a json array. Each element of the array is a dict containing a query to get relevant information from the database, and a description of the result.
        Queries must be permissive: they should be case insensitive and allow for typos.
        If you have to do any calculations, do them directly in the query.
        
        ## Example 1

        ### Question
        How old is John Doe?

        ### Answer
        {{"queries": [ {{"query":"SELECT age FROM users WHERE UPPER(name) = UPPER('John Doe')","description":"Age of John Doe:"}}
        
        ## Example 2

        ### Question
        What are the orders of user 1?
        
        ### Answer
        {{"query":"SELECT * FROM orders WHERE user_id = 1","description":"All orders of user with id 1:"}} ]}}
        
        ## Example 3
        ### Question
        Hello!

        ### Answer
        {{"queries": []}} 

        ## User Request

        ### Database Information
        {db_manager.print_database_info(db_manager.get_database_info())}

        ### Question
        {user_message}

        ### Answer
    """.strip()


def get_queries_from_output(output: str) -> List[str]:
    return json.loads(output["output"])["queries"]


def process_queries(cat, queries: List[str]) -> str:
    settings = cat.mad_hatter.plugins["db_gpt"].load_settings()
    db_manager = DatabaseManager(db_uri=settings["db_uri"])
    db_augmented_context = ""
    for query in queries:
        log.info(f"Executing query: {query}")
        result = db_manager.execute_query(query["query"])
        print("RESULTS")
        print(result)
        db_augmented_context += f"{query['description']} {result}\n"
    return db_augmented_context


def enrich_user_message_with_db_context(user_message_json: dict, db_augmented_context: str) -> str:
    return f"""
        ### Database Retrieved Data
        {db_augmented_context}

        ### User Request
        {user_message_json["text"]}
    """.strip()