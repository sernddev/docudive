class DataframeInMemorySQLExecutionException(Exception):
    def __init__(self, base_exception, message="A custom exception occurred"):
        self.message = message
        self.base_exception = base_exception
        super().__init__(self.message, self.base_exception)

    def __str__(self):
        return f"{self.__class__.__name__}({self.args[0]}, code={self.base_exception})"


class LLMException(Exception):
    def __init__(self, base_exception, message="A custom LLM exception occurred"):
        self.message = message
        self.base_exception = base_exception
        super().__init__(self.message, self.base_exception)

    def __str__(self):
        return f"{self.__class__.__name__}({self.args[0]}, code={self.base_exception})"
