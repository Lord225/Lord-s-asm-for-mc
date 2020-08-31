class BadThread(Exception):
    def __init__(self, info:str):
        self.info = info  
    def __str__(self):
         return "This thread is invalid: '{}'".format(self.info)  
class ExpectedValue(Exception):
    def __init__(self, n, info:str):
        self.info = info    
        self.MAX = 2**n-1
        self.n = n
    def __str__(self):
         return "Expected bit value (<0,{}> range), got: {}".format(self.n, self.MAX, self.info)
class UndefinedValue(Exception):
    def __init__(self, info = ""):
        self.info = info 
    def __str__(self):
         return "Invalid value: {}".format(self.info)  
class UndefinedCommand(Exception):
    def __init__(self, info = ""):
        self.info = info 
    def __str__(self):
         return "Undefine opcode: {}".format(self.info)  
class SynaxError(Exception):
    def __init__(self, expected = "", got=""):
        self.expected = expected 
        self.got = got 
    def __str__(self):
         return "Expected: {}, got: {}".format(self.expected, self.got)  
class UnexpectedArgumentTypes(Exception):
    def __init__(self, info = ""):
        self.info = info 
    def __str__(self):
         return "Unexpected argument types: {}".format(self.info)
class Unsupported(Exception):
    def __init__(self, info = ""):
        self.info = info 
    def __str__(self):
         return "This is currently unsupported: {}".format(self.info)
class UndefinedIdentifier(Exception):
    def __init__(self, info = ""):
        self.info = info 
    def __str__(self):
         return "Jump identifier: '{}' is undefined".format(self.info)
class UndefinedSetting(Exception):
    def __init__(self, info = ""):
        self.info = info 
    def __str__(self):
         return "This setting value is unvalid: {}".format(self.info)
class StackOverFlowError(Exception):
    def __init__(self, info = ""):
        self.info = info 
    def __str__(self):
         return "Stack overflow: {}".format(self.info)
class StackUnderFlowError(Exception):
    def __init__(self, info = ""):
        self.info = info 
    def __str__(self):
         return "Stack underflow: {}".format(self.info)
class LoadError(Exception):
    def __init__(self, info = ""):
        self.info = info 
    def __str__(self):
         return "Load Error: {}".format(self.info)
class ProfileStructureError(Exception):
    def __init__(self, info = ""):
        self.info = info 
    def __str__(self):
         return "profile structure is unvalid: {}".format(self.info)