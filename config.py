import core.error as err

#GLOBAL CONFIGS

#SETTINGS (argparser > file_settings > config > default)
def setupsettings(parserargs, config_name, file_settings):
    print("Loading Settings:")
    
    #default
    FILE_NAME = "Program.lor"
    PROFILE_NAME = None
    ACTION = "build"
    OUTPUT_FILE = "compiled.txt"
    LOG_INFOO = None
    ACTION_ON_ERROR = None
    BUILD_OFFSET = 0
    SPEED = -1
    CONSTS = []
    SAVE_IN_ONE_FILE = False
    LOG_COMMAND_MODE = None
    RAM_DEBUG_MODE = "row"
    LOG_COMMAND_MODE = "short" 
    USE_FANCY_SYNAX = True
    RAISE_ERROR_ON_NOT_IMPLEMENTED_BIN_FORMATING = False
    RAISE_ERROR_ON_NOT_IMPLEMENTED_EMULATOR = True
    DEBUG_MODE = "simple"

    USE_DATA_BLOCKS = True
    DEFAULT_PROFILES_PATH = "profiles"
    G_RISE_ERROR_ON_BAD_RANGES = False      # [True, False] if bad range appears, the error will be rised. 
    FORCE_COMMANDS_IN_SEPERATE_ROWS = True  # commands will always be in seperate rows
    CHECK_ROM_SIZE = -1                     # int           if not -1 compiler will check if program is bigger that hardwere rom
    IGNORE_DEBUG_COMMANDS = False           # [True, False] if true debug commands will be ignored
    IGNORE_EMPTY_PROGRAMS = True            # [True, False] if sector is empty, will not be saved.
    
    CPYTHON_PROFILING = False               # [True, False] 
    TIME_MILTIPLAYER = 0.5                  # float         
    SHOW_RAW_PROGRAM = False                # [True, False] 
    DEFINITION_DEBUG = False                # [True, False] 
    

    #config
    if config_name is not None:
        print("Loading '{}'".format(config_name))
        with open(config_name, "r") as file:
            for line in file:
                NAME, DATA = (txt.strip() for txt in line.split("="))
                if NAME in locals():
                    locals()[NAME] = DATA
                else:
                    raise err.LoadError("Canno't find setting {}".format(NAME))
        try:
            SPEED = int(SPEED)
        except:
            raise err.LoadError("Canno't interetate SPEED")

    #file settings
    if file_settings is not None:
        print("Loading file settings")

    #argparser
    if parserargs is not None:
        print("Parsing arguments")
        FILE_NAME            = FILE_NAME        if parserargs.file is None else parserargs.file
        PROFILE_NAME         = PROFILE_NAME     if parserargs.profile is None else parserargs.profile
        ACTION               = ACTION           if parserargs.action is None else parserargs.action
        OUTPUT_FILE          = OUTPUT_FILE      if parserargs.outfile is None else parserargs.outfile
        LOG_INFOO            = LOG_INFOO        if parserargs.info is None else parserargs.info
        ACTION_ON_ERROR      = ACTION_ON_ERROR  if parserargs.onerror is None else parserargs.onerror
        BUILD_OFFSET         = BUILD_OFFSET     if parserargs.offset is None else parserargs.offset
        SPEED                = parserargs.speed if -1 <= parserargs.speed < 1000 else SPEED
        CONSTS               = CONSTS           if parserargs.const is None else parserargs.const
        SAVE_IN_ONE_FILE     = CONSTS           if parserargs.onefile is None else True
        LOG_COMMAND_MODE     = LOG_COMMAND_MODE if parserargs.logmode is None else parserargs.logmode
        RAM_DEBUG_MODE       = RAM_DEBUG_MODE

    globals().update(locals())        
setupsettings(None, None, None)