#Public domain, free to use, by Lord255 aka M. Złotorowicz
VERSION = "0.7"

import math as m
import random as rnd
import core.loading as loading
import core.interpreter_synax_solver as iss
import core.error as error
import argparse
import os
import time

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

# -f -a -o -l -i -e -of -s --const
parser.add_argument("-f", "--file", type=str, default="Program.lor",  #TODO FIX WITH RELATIVE DIR
help="""Name of file to proces
Default: Program.lor
""")
parser.add_argument("-a", "--action", choices=["build", "compile-dec", "compile-csv", "compile-bin", "compile-py" , "refactor", "interprate"], type=str, default="build",
help="""What script is supposed to do with file 
> build         - Build source and execute 
> compile-dec   - Build source and save in easy-to-read format
> compile-csv   - Build source and save as csv
> compile-bin   - Build source and save as binary
> compile-py    - Build source and save as python dict
> refactor      - Build source and save as redable commands
> interprate    - Execute without building (interpretate command in runtime) (deprecated)
Default: build
""")
parser.add_argument("-p",'--profile', type=str, default="None",
help="""Parse CPU profile""")
parser.add_argument("-o", "--outfile", type=str, default="compiled.txt", help="Name of binary to save")
parser.add_argument("-l", "--logmode", choices=["short", "long","None"], type=str, default="None",
help="""Choose method of logging CPU's command while executing
> short - Simple logging
> long  - Full logging
> None  - No logging
Default: None
""")
parser.add_argument("-i", "--info", choices=["warnings", "errors", "both", "None"], type=str, default="None",
help="""Choose CPU warning level
> warnings  - Warnings only
> errors    - Errors only
> both      - Errors and warnings
> None      - No CPU warnings in console
Default: None
""")
parser.add_argument("-e", "--onerror", choices=["interupt", "abort", "None"], type=str, default="None", 
help="""What is suppouse to happen on error
> interupt - Waits for user
> abort    - Close script
> None     - Throw python's error
Default: abort
""")
parser.add_argument("-of", "--offset", type=int, default=1, 
help="""Offset of whole binary relative to rom 0 cell
Default: 1 (first command on pos 1 second on 2 ect)
""")
parser.add_argument("-s", "--speed", type=int, default=-1, 
help="""Execution speed in hertz (-1 - maximal possible)
Default: -1
""")
parser.add_argument('--const', action='append', 
help="""Addinationl const expressions added while loading script
 Format:
 --const NAME_OF_CONSTANT VALUE (COULD BY LONG AND WITH SPACES)
 --const JUST_NAME_MEANS_DEFINITION
""")
parserargs = parser.parse_args()

#SETTINGS (argparser > file_settings > default)
FILE_NAME = parserargs.file
PROFILE_NAME =  parserargs.profile
ACTION = parserargs.action
OUTPUT_FILE = parserargs.outfile
iss.LOG_COMMAND_MODE = None if parserargs.logmode == "None" else parserargs.logmode
iss.RAM_DEBUG_MODE = "row"
LOG_INFOO = None if parserargs.info == "None" else parserargs.info
ACTION_ON_ERROR = None if parserargs.onerror == "None" else parserargs.onerror
BUILD_OFFSET = parserargs.offset
SPEED = parserargs.speed if -1 <= parserargs.speed < 1000 else -1
CONSTS = [] if parserargs.const is None else parserargs.const
DEFAULT_PROFILES_PATH = "profiles"
USE_DATA_BLOCKS = True

#low priority
iss.G_RISE_ERROR_ON_BAD_RANGES = False  # [True, False]
iss.FORCE_COMMANDS_IN_SEPERATE_ROWS = True
CHECK_ROM_SIZE = -1                     # int
IGNORE_DEBUG_COMMANDS = False           # [True, False]

#DEBUG
CPYTHON_PROFILING = False               # [True, False]
TIME_MILTIPLAYER = 0.5                  # float 
SHOW_RAW_PROGRAM = False                # [True, False]
loading.DEFINITION_DEBUG = False        # [True, False]

PROCESSED_LINE = -1

# TODO
#*coding to binary\
# gpu
#*multiline definitions
# threads rolling
#*push pop commands
#*parsering definitions
#*FIX JUMP OFFSET (NOW IT COUNT 0)
# insert raw (#insert {ANY BINARY ASSEMBLY DATA})
#*advanded ram debugging (like in vs2019 (with adresses ect.))
# performance profiling tools (with loops times ect)
# generalize jump statements with new approch
#*info logging
#*datablocks:
#*#DATA 0x00 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
#*      ^^^^ ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#*      start adress      numbers to write
#*FIX OFFSET (it should be -1 or NOT)
#*macros
# better macros (with definition and refining in fly)
# precise arg maching (without matching xor as or ect)

#?parsering low priority settings

if ACTION == "everything":
    raise error.CurrentlyUnsupported("ACTION->everything")

    

def get_profile(NAME):
    global CONSTS
    CPU_PROFILE = loading.load_json_profile('{}/{}'.format(DEFAULT_PROFILES_PATH, NAME))

    exec("import {}.{} as emulator".format(DEFAULT_PROFILES_PATH, CPU_PROFILE["CPU"]["emulator"]), globals())
    iss.emul = emulator
    try:
        print("Loaded profile for: '{}' by {}".format(CPU_PROFILE["CPU"]["Name"], CPU_PROFILE["CPU"]["Author"]))
        CONSTS.extend(CPU_PROFILE["CPU"]["DEFINES"])
    except KeyError as key:
        print("Can't find key in profile: {}".format(key))
        return
    except:
        print("Error: module {} doesn't exists.".format(CPU_PROFILE["CPU"]["emulator"]))
        return
    
    iss.extract_basic_data(CPU_PROFILE)

    COMMAND_COUNTER = [0 for _ in range(4)]
    DEVICE = emulator.CPU()

    return CPU_PROFILE, COMMAND_COUNTER, DEVICE

def setupsettings():
    pass

def main():
    global PROFILE_NAME
    print("CPU Assembly tools for minecraft by M. Złotorowicz aka Lord225. 2020")
    print("")

    def end_sequence():
        time_end = time.thread_time_ns()
        TOTAL = (time_end-time_start)/1000000000.0
        PER_CMD = 0.0
        if COMMAND_COUNTER[core_id] != 0:
            PER_CMD = (time_end-time_start)/(COMMAND_COUNTER[core_id]*1000000)
        print("="*50)
        print("Core {} finished work ({} ticks, apr. {}s on device)".format(core_id, COMMAND_COUNTER[core_id], COMMAND_COUNTER[core_id]*TIME_MILTIPLAYER))
        print("Total execution time: {:0.4f}s, {:0.3f} ms per command".format(PER_CMD, PER_CMD))
        actives.remove(active)

    #################################################
    #                     LOADING                   #
    #################################################

    load_start_time = time.thread_time_ns()
    print("Loading {}, with consts: {}".format(FILE_NAME, CONSTS))

    Program, line_indicator, JUMPLIST, Settings, data = loading.load_program(FILE_NAME, CONSTS) #first pass
    
    #Find CPU profile
    if PROFILE_NAME == "None" and "PROFILE" in Settings:
        PROFILE_NAME = Settings["PROFILE"]
    if PROFILE_NAME == "None":
        raise error.LoadError("Please parse profile for cpu.")
    
    #GET PROFILE AND DEVICE
    CPU_PROFILE, COMMAND_COUNTER, DEVICE = get_profile(PROFILE_NAME)

    print("Reloading {}, with consts: {}".format(FILE_NAME, CONSTS))
    
    #reload with extended consts.
    Program, line_indicator, JUMPLIST, Settings, data = loading.load_program(FILE_NAME, CONSTS) #second pass

    actives = loading.find_executable_cores(Program)
    
    setupsettings()
    
    if ACTION == "interprete":
        print("WARNING: 'interprete' functionality is now deprecated. Do not use it.")

    #################################################
    #                   COMPILING                   #
    #################################################
    
    if SHOW_RAW_PROGRAM:
        print("Program:", Program, "\n\nJUMPLIST:", JUMPLIST, "\n\nSettings:", Settings, "\n\nActives Cores:", actives)

    time_start = time.thread_time_ns()

    print("Total load time: {}ms".format((time_start-load_start_time)/1000000))

    if ACTION in ["build", "compile-dec", "compile-csv", "compile-bin", "compile-py", "refactor"]:
        #compile
        builded = iss.build_program(Program, line_indicator, JUMPLIST, Settings)
        if ACTION[:len("compile")] == "compile":
            to_save = iss.get_compiled(builded, BUILD_OFFSET)
        elif ACTION == "refactor":
            to_save = iss.form_full_log_command_batch(builded, BUILD_OFFSET)

        #info
        total_command_count = sum([len(x) for x in Program.values()])
        time_end = time.thread_time_ns()
        TOTAL = (time_end-time_start)/1000000.0
        PER_CMD = 0.0
        if total_command_count != 0:
            PER_CMD = (time_end-time_start)/(total_command_count*1000000.0)

        print("="*50)
        print("Builded {} commands".format(total_command_count))
        print("Total build time: {:0.4f}ms, {:0.3f} ms per command".format(TOTAL, PER_CMD))
        
        #################################################
        #                     SAVE                      #
        #################################################
        
        if ACTION == "compile-dec": 
            to_save = iss.get_dec(to_save)
            loading.save(OUTPUT_FILE, to_save)
        elif ACTION == "compile-csv":
            to_save = iss.get_csv(to_save)
            loading.save(OUTPUT_FILE, to_save, with_decorators = False)
        elif ACTION == "compile-bin": 
            to_save = iss.get_bin(to_save)
            loading.save(OUTPUT_FILE, to_save)
        elif ACTION == "refactor":
            loading.save(OUTPUT_FILE, to_save)
        
        #CHECK INFO AND WARNINGS
        if (LOG_INFOO == "warnings" or LOG_INFOO == "both") and len(iss.G_INFO_CONTAINER["info"]) > 0:
            print("info:", iss.G_INFO_CONTAINER["info"])
        if (LOG_INFOO == "errors" or LOG_INFOO == "both") and len(iss.G_INFO_CONTAINER["warnings"]) > 0:
            print("warnings:", iss.G_INFO_CONTAINER["warnings"])

        #end
        if ACTION != "build":
            print("="*50)
            return


    #################################################
    #                  EMULATING                    #
    #################################################

    if USE_DATA_BLOCKS:
        for adress, value in data.items():
            try:
                DEVICE.RAM[adress] = value
            except Exception as err:
                raise error.LoadError("Error while parsing data to device: {}".format(err))
    while True:
        for active in actives:
            core_id = loading.CORE_ID_MAP[active]
            
            #GET AND EXECUTE COMMAND            
            if ACTION == "build":
                try:
                    CPU_COMMAND = builded[active][DEVICE.get_rom_adress(core_id)]
                    PROCESSED_LINE = line_indicator[active][DEVICE.get_rom_adress(core_id)]
                except IndexError:
                    end_sequence()
                    continue
                if type(CPU_COMMAND) is list:
                    for thread, (_type, formed_command, args) in enumerate(CPU_COMMAND):
                        info = iss.execute(_type, formed_command, DEVICE, core_id, args, thread)
                    if iss.LOG_COMMAND_MODE is not None and not iss.FORCE_COMMANDS_IN_SEPERATE_ROWS:
                        print()
                else:
                    _type, formed_command, args = CPU_COMMAND
                    info = iss.execute(_type, formed_command, DEVICE, core_id, args, None)
            else:
                #old, interprete
                try:
                    command = Program[active][DEVICE.get_rom_adress(core_id)]
                except IndexError:
                    end_sequence()
                    continue
                
                info = iss.read_and_execute(DEVICE, JUMPLIST[active], core_id, command)


            #CHECK INFO AND WARNINGS
            if (LOG_INFOO == "warnings" or LOG_INFOO == "both") and len(info["info"]) > 0:
                print("info:", info["info"])
            if (LOG_INFOO == "errors" or LOG_INFOO == "both") and len(info["warnings"]) > 0:
                print("warnings:", info["warnings"])
            
            
            #CHECK PERFORMANCE
            if not info["skip"]:
                COMMAND_COUNTER[core_id] += 1
            DEVICE.end_tick(core_id)
            
            #STOP FLAG
            if info["stop"]:
                end_sequence()

        #END CPU TICK
        DEVICE.end_cpu_tick()
        if SPEED != -1:
            time.sleep(1/SPEED)

        
        if len(actives) == 0:
            print("All cores did their duty.")
            #exit
            break
    
if __name__ == "__main__":
    if CPYTHON_PROFILING:
        import cProfile
        cProfile.run("main()", sort="cumtime")
    else:
        if ACTION_ON_ERROR is None:
            main()
        else:
            try:
                main()
            except Exception as err:
                print("*"*50)
                try:
                    print("Error in line {}:".format(err.line))
                except:
                    if PROCESSED_LINE != -1:
                        print("Error in line {}:".format(PROCESSED_LINE))
                    else:
                        print("Error in unknown line:")
                print("Error:", err)
                
                if ACTION_ON_ERROR == "interupt":
                    input()
                elif ACTION_ON_ERROR == "abort":
                    pass