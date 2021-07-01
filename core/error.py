class BadThread(Exception):
    def __init__(self, info:str):
        self.info = info  
    def __str__(self):
         return "Invalid Thread: {}".format(self.info)  
class UndefinedValue(Exception):
    def __init__(self, info = ""):
        self.info = info 
    def __str__(self):
         return "Invalid value: {}".format(self.info)  
class UndefinedCommand(Exception):
    def __init__(self, info = ""):
        self.info = info 
    def __str__(self):
         return "Undefine command: {}".format(self.info)  
class SynaxError(Exception):
    def __init__(self, error = ""):
        self.error = error 
    def __str__(self):
         return "Synax error: {}".format(self.error)
class Expected(Exception):
    def __init__(self, expected = "", got=""):
        self.expected = expected 
        self.got = got 
    def __str__(self):
         return "Expected: '{}', got: '{}'".format(self.expected, self.got)  
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
class EmulatorError(Exception):
    def __init__(self, info = "Unspecified"):
        self.info = info 
    def __str__(self):
         return "EmulationError: {}".format(self.info)
class LoadError(Exception):
    def __init__(self, info = ""):
        self.info = info 
    def __str__(self):
         return "Load Error: {}".format(self.info)
class ProfileStructureError(Exception):
    def __init__(self, info = "", custom = True):
        self.info = info 
        self.custom = custom
    def __str__(self):
        if not self.custom:
            return "Profile structure is unvalid, Expected key: {}".format(self.info)
        else:
            return "Profile structure is unvalid: {}".format(self.info)
class DeprecatedFunction(Exception):
    def __init__(self, info = ""):
        self.info = info 
    def __str__(self):
         return "This function is now deprecated: {}".format(self.info)
         