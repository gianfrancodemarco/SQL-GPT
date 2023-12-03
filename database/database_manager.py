
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class DatabaseManager:
    def __init__(self, db_uri):
        self.engine = create_engine(db_uri)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def execute_query(self, query):
        session = self.Session()
        # Return result as dict 
        result = session.execute(text(query)).all()
        session.commit()
        session.close()
        return result

    def get_database_info(self):
        inspector = inspect(self.engine)
        tables_info = {}

        for table_name in inspector.get_table_names():
            columns_info = {column["name"]: str(
                column["type"]) for column in inspector.get_columns(table_name)}
            tables_info[table_name] = columns_info

        return tables_info

    def print_database_info(self):
        pretty_print = ""
        for table, columns in self.get_database_info().items():
            pretty_print += f"Table: {table}\n"
            for column, data_type in columns.items():
                pretty_print += f" {column}: {data_type}\n"
            pretty_print += "\n"
        return pretty_print
