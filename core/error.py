
class CompilerError(Exception):
    def __init__(self, line_number: int, info: str, *args: object) -> None:
        super().__init__(*args)
        self.line = line_number
        self.info = info
        self.stage = None
        

# Derives

class PreprocesorError(CompilerError):
    def __init__(self,  line_number: int, info: str, *args: object) -> None:
        super().__init__(line_number, info, *args)
        self.stage = None

    def __str__(self):
         return f"Preprocesing error: {self.info}"

class ParserError(CompilerError):
    def __init__(self,  line_number: int, info: str, *args: object) -> None:
        super().__init__(line_number, info, *args)

    def __str__(self):
         return f"Parsing error: {self.info}"
class UnparsableTokenError(CompilerError):
    def __init__(self, info: str, expected_type: str, *args: object) -> None:
        super().__init__(None, info, *args)
        self.expected_type = expected_type

    def __str__(self):
         return f"Token: '{self.info}' cannot be parsed as '{self.expected_type}'"

class ProfileLoadError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

