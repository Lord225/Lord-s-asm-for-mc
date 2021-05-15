import core.error as errors

class CONFIG_LIST:
    def __init__(self) -> None:
        self.FILE_NAME = "src/program.lor"
        self.PROFILE_NAME = None
        self.SAVE = "red"
        self.RUN = False
        self.COMMENTS = False
        self.OUTPUT_FILE = "compiled.txt"
        self.LOG_INFOO = None
        self.ACTION_ON_ERROR = None
        self.BUILD_OFFSET = 0
        self.SPEED = -1
        self.CONSTS = []
        self.SAVE_IN_ONE_FILE = False
        self.LOG_COMMAND_MODE = None
        self.RAM_DEBUG_MODE = "row"
        self.LOG_COMMAND_MODE = "long" 
        self.USE_FANCY_SYNAX = True
        self.RAISE_ERROR_ON_NOT_IMPLEMENTED_BIN_FORMATING = False
        self.RAISE_ERROR_ON_NOT_IMPLEMENTED_EMULATOR = True
        self.DEBUG_MODE = "simple"

        self.USE_DATA_BLOCKS = True
        self.DEFAULT_PROFILES_PATH = "profiles"
        self.G_RISE_ERROR_ON_BAD_RANGES = False      # [True, False] if bad range appears, the error will be rised. 
        self.FORCE_COMMANDS_IN_SEPERATE_ROWS = True  # commands will always be in seperate rows
        self.CHECK_ROM_SIZE = -1                     # int           if not -1 compiler will check if program is bigger that hardwere rom
        self.IGNORE_DEBUG_COMMANDS = False           # [True, False] if true debug commands will be ignored
        self.IGNORE_EMPTY_PROGRAMS = True            # [True, False] if sector is empty, will not be saved.

        self.CPYTHON_PROFILING = False               # [True, False] 
        self.TIME_MILTIPLAYER = 0.5                  # float         
        self.SHOW_RAW_PROGRAM = False                # [True, False] 
        self.DEFINITION_DEBUG = False                # [True, False] 

# SETTINGS PRIORITY (argparser > file_settings > config > default)
def setupsettings(parserargs, config_name, file_settings):
    print("Loading Settings:")

    config = CONFIG_LIST()

    def refine(data, new_data = None):
        if new_data is not None or new_data == "None":
            data = new_data
        if data == "False" or data == "True":
            data = False if data == "False" else True
        data = None if data == "None" else data
        if type(data) is str:
            try:
                data = int(data)
            except:
                try:
                    data = float(data)
                except:
                    pass
        return data

    # Config
    if config_name is not None:
        print("Loading '{}'".format(config_name))
        with open(config_name, "r") as file:
            for line in file:
                # Clean up
                line = line[:line.find("#")]
                if len(line) == 0 or line.find("=") == -1:
                    continue
                NAME, DATA = (txt.strip() for txt in line.split("="))

                if NAME in vars(config):
                    DATA = refine(DATA)
                    try:
                        vars(config)[NAME] = DATA
                    except Exception as err:
                        raise errors.LoadError("Canno't use setting {} or value '{}' is not valid".format(NAME, DATA))

                else:
                    raise errors.LoadError("Canno't find setting {}".format(NAME))

    # File Settings
    if file_settings is not None:
        print("Loading file settings")

    # Argparser
    if parserargs is not None:
        print("Parsing arguments")
        config.FILE_NAME            = refine(config.FILE_NAME,        parserargs.file)
        config.PROFILE_NAME         = refine(config.PROFILE_NAME,     parserargs.profile) 
        config.SAVE                 = refine(config.SAVE,             parserargs.save)      
        config.RUN                  = refine(config.RUN,              parserargs.run)
        config.COMMENTS             = True if parserargs.comments == True else False  
        config.OUTPUT_FILE          = refine(config.OUTPUT_FILE,      parserargs.outfile)
        config.LOG_INFOO            = refine(config.LOG_INFOO,        parserargs.info)       
        config.ACTION_ON_ERROR      = refine(config.ACTION_ON_ERROR,  parserargs.onerror)
        config.BUILD_OFFSET         = refine(config.BUILD_OFFSET,     parserargs.offset)
        config.CONSTS               = refine(config.CONSTS,           parserargs.const)
        config.SAVE_IN_ONE_FILE     = refine(config.SAVE_IN_ONE_FILE, parserargs.onefile)  
        config.LOG_COMMAND_MODE     = refine(config.LOG_COMMAND_MODE, parserargs.logmode)
        config.RAM_DEBUG_MODE       = config.RAM_DEBUG_MODE

    globals().update(vars(config))
  
setupsettings(None, None, None)