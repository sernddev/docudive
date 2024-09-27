class PromptGenerationException(Exception):
    def __init__(self, base_exception, message="An exception occurred while generating the prompt"):
        self.message = message
        self.base_exception = base_exception
        super().__init__(self.message, self.base_exception)

    def __str__(self):
        return f"{self.__class__.__name__}({self.args[0]}, code={self.base_exception})"
