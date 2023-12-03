from cat.plugins.sql_gpt.database.database_manager import DatabaseManager
from abc import ABC, abstractmethod
from typing import List, Dict
import json
from cat.looking_glass.cheshire_cat import CheshireCat


class Solver(ABC):

    def __init__(
        self,
        database_manager: DatabaseManager,
    ) -> None:
        self.database_manager = database_manager

    def solve(
        self,
        user_message: str
    ):
        prefix, suffix = self.build_message()
        output = self.ask_lmm(
            user_message,
            prefix,
            suffix
        )
        queries = self.get_queries_from_output(output)
        db_answer = self.process_queries(queries)
        return db_answer

    @abstractmethod
    def ask_lmm(
        self,
        user_message: str,
        prefix: str,
        suffix: str
    ) -> Dict:
        pass

    def build_message(self):
        prefix = """
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
            {{"queries": [{{"query": "SELECT age FROM users WHERE UPPER(name) = UPPER('John Doe')","description":"Age of John Doe:"}}]}}
            
            ## Example 2

            ### Question
            What are the orders of user 1?
            
            ### Answer
            {{"queries": [{{"query": "SELECT * FROM orders WHERE user_id = 1","description":"All orders of user with id 1:"}}]}}
            
            ## Example 3
            ### Question
            Hello!

            ### Answer
            {{"queries": []}}
        """

        suffix = f"""
            ## User Request

            ### Database Information
            {self.database_manager.print_database_info()}

            ### Question
            {{input}}

            ### Answer
        """

        return prefix, suffix

    def get_queries_from_output(output: str) -> List[str]:
        return json.loads(output["output"])["queries"]

    def process_queries(
        self,
        queries: List[str]
    ) -> str:
        db_augmented_context = ""
        for query in queries:
            result = self.database_manager.execute_query(query["query"])
            db_augmented_context += f"{query['description']} {result}\n"
        return db_augmented_context


class CatSolver(Solver):

    def __init__(
        self,
        cat: CheshireCat
    ) -> None:
        self.cat = cat

    def ask_llm(
        self,
        user_message: str,
        prefix: str,
        suffix: str,
    ):
        agent_input = {
            "input": user_message,
            "episodic_memories": [],
            "declarative_memory": "",
            "chat_history": ""
        }

        cat_message = self.cat.agent_manager.execute_memory_chain(
            agent_input=agent_input,
            prompt_prefix=prefix,
            prompt_suffix=suffix,
            working_memory=""
        )
        return cat_message
