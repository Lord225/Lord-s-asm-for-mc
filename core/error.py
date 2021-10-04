
class CompilerError(Exception):
    def __init__(self, line_number: int, info: str, *args: object) -> None:
        super().__init__(*args)
        self.line = line_number
        self.info = info
        

# Derives

class PreprocesorError(CompilerError):
    def __init__(self,  line_number: int, info: str, *args: object) -> None:
        super().__init__(line_number, info, *args)

    def __str__(self):
         return f"Preprocesing error: {self.info}"
