class ContextManager:
    def __init__(self):
        self.context: dict = {}

    def add_to_context(self, step_name: str, output: dict):
        self.context[step_name] = output

    def get_context(self) -> dict:
        return self.context

    def clear_context(self):
        self.context = {}

context_manager = ContextManager()
