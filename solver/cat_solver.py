from cat.looking_glass.cheshire_cat import CheshireCat


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
