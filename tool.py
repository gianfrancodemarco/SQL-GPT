from cat.mad_hatter.decorators import hook, tool
from cat.plugins.sql_gpt.database import DatabaseManager, TestDatabaseManager
from cat.plugins.sql_gpt.solver import CatSolver
from cat.plugins.sql_gpt.settings import SQLGPTSettings
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

solver = None
db_manager = None


@tool
def retrieve_db_info(user_message, cat) -> str:
    """
    Useful to retrieve database information to answer user questions.
    The input is the complete user request.
    Call this if the user asks for information or calculations that require database information, for example
    "How many users are there?", "What is the average age of users in the DB?", "How many orders are there?",
    "Give me the total amount of orders", "What is the average amount of orders?", "What is the average amount of orders per user?"
    """

    return solver.solve(user_message)


@hook
def before_embed_tool(tool_description: str, tool_name: str, cat) -> None:
    global db_manager
    if tool_name == retrieve_db_info.name:
        tool_description += db_manager.print_database_info()
    return tool_description


@hook
def before_cat_bootstrap(cat) -> None:
    global db_manager, solver

    settings: SQLGPTSettings = cat.mad_hatter.plugins["sql_gpt"].load_settings(
    )

    if settings["test_db"]:
        db_manager = TestDatabaseManager(db_uri=settings["db_uri"])
        db_manager.drop_tables()
        db_manager.create_tables()
        db_manager.insert_sample_data()
    else:
        db_manager = DatabaseManager(db_uri=settings["db_uri"])

    solver = CatSolver(
        db_manager=db_manager,
        cat=cat
    )


@hook
def agent_prompt_prefix(prefix, cat) -> str:
    return """
    You are an AI assistant which is able to access relational databases to answer questions.\n\n
    """