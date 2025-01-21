from typing import Optional

class CompilerError(Exception):
    def __init__(self, line_number: Optional[int], info: str, line_object: object=None, *args: object) -> None:
        super().__init__(*args)
        self.line = line_number
        self.info = info
        self.line_object = line_object
        self.stage = None

class PreprocesorError(CompilerError):
    def __init__(self,  line_number: Optional[int], info: str, *args: object) -> None:
        super().__init__(line_number, info, *args)
        self.stage = None

    def __str__(self):
         return f"Preprocesing error: {self.info}"

class ParserError(CompilerError):
    def __init__(self,  line_number: Optional[int], info: str, line_object: object=None, *args: object) -> None:
        super().__init__(line_number, info, line_object, *args)

    def __str__(self):
         return f"Parsing error: {self.info}"

class ProfileLoadError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
 
class EmulationError(Exception):
    def __init__(self, msg: str, *args: object) -> None:
        super().__init__(*args)
        self.msg = msg
    def __str__(self):
         return f"Emulator Error: {self.msg}"
