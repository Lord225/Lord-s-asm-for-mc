#Public domain, free to use, by M. Złotorowicz aka Lord255
VERSION = "1.0"

import math as m
import random as rnd
from typing import cast
import core.loading as loading
import core.interpreter_synax_solver as iss
import core.error as error
import argparse
import time
import core.config as config

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

# -f -a -o -l -i -e -of -s --const --onefile
parser.add_argument("-f", "--file", type=str, default="src/program.lor", 
help="""Name of file to compile
Default: src/program.lor
""")
parser.add_argument("-s", "--save", choices=["dec", "raw", "bin", "py"], type=str, default = None,
help="""
> dec - Build source and save in easy-to-read format
> raw - Build source and save as binary with padding to halfbytes
> bin - Build source and save as binary with padding to arguments
> py  - Build source and save as python dict
Default: None (will not save)
""")
parser.add_argument('-c','--comments', dest='comments', action='store_true')
parser.set_defaults(feature=False)

parser.add_argument('-r', '--run', dest='run', action='store_true')
parser.set_defaults(feature=False)

parser.add_argument('--profile', type=str, default=None,
help="""Parse CPU profile. If you have to use that, you did something wrong.""")
parser.add_argument("-o", "--outfile", type=str, default="compiled/compiled.txt", help="Name of binary to save")

parser.add_argument('--logs', dest='logmode', action='store_true', help="Choose method of logging CPU's command while executing")
parser.set_defaults(feature=False)

parser.add_argument("-i", "--info", choices=["warnings", "errors", "both", "None"], type=str, default = None,
help="""Choose CPU warning level
> warnings  - Warnings only
> errors    - Errors only
> both      - Errors and warnings
> None      - No CPU warnings in console
Default: None
""")
parser.add_argument("--onerror", choices=["interupt", "abort"], type=str, default = None, 
help="""What is suppouse to happen on error
> interupt - Waits for user
> abort    - Close script
> None     - Throw python error
Default: None
""")
parser.add_argument("--offset", type=int, default=0, 
help="""Offset of whole binary relative to rom 0 cell
Default: 0 (first command on pos 0 second on 1 ect)
""")
parser.add_argument('--const', action='append', 
help="""Addinationl const expressions added while loading script
 Format:
 --const NAME_OF_CONSTANT VALUE (COULD BY LONG AND WITH SPACES)
 --const JUST_NAME_MEANS_DEFINITION
""")
parser.add_argument('--onefile',  type=bool, default=False, 
help="""Saves output from diffrent cores in same file""")
parserargs = parser.parse_args()

ACTION_ON_ERROR = None #[None, 'interupt', 'abort']
ACTION_ON_ERROR = ACTION_ON_ERROR if parserargs.onerror is None else parserargs.onerror

PROCESSED_LINE = -1


def main():
    global PROCESSED_LINE
    print("CPU Assembly tools for minecraft by M. Złotorowicz aka Lord225. 2021\n")

    #################################################
    #                     LOADING                   #
    #################################################

    load_start_time = time.thread_time_ns()

    program, jump_list, file_settings, actives, line_indicator, data, DEVICE, COMMAND_COUNTER = double_pass_program_loading()

    compile_start = time.thread_time_ns()
    print("Total load time: {}ms".format((compile_start-load_start_time)/1000000))

    if config.SHOW_RAW_PROGRAM:
        print("Program:", program, "\n\nJUMPLIST:", jump_list, "\n\nSettings:", file_settings, "\n\nActives Cores:", actives)

    #################################################
    #                   COMPILING                   #
    #################################################
    

    built = iss.build_program(program, line_indicator, jump_list, file_settings)
    compiled = iss.get_compiled(built, config.BUILD_OFFSET)

    compile_end_time = time.thread_time_ns()
    total_command_count, TOTAL, PER_CMD = get_build_telemetry_times(program, compile_start, compile_end_time)
    print("="*50)
    print("built {} commands".format(total_command_count))
    print("Total build time: {:0.4f}ms, {:0.3f} ms per command".format(TOTAL, PER_CMD))
    
    #################################################
    #                     SAVE                      #
    #################################################
    
    save(jump_list, built, compiled)

    
    # CHECK INFO AND WARNINGS
    if (config.LOG_INFOO == "warnings" or config.LOG_INFOO == "both") and len(iss.G_INFO_CONTAINER["info"]) > 0:
        print("info:", iss.G_INFO_CONTAINER["info"])
    if (config.LOG_INFOO == "errors" or config.LOG_INFOO == "both") and len(iss.G_INFO_CONTAINER["warnings"]) > 0:
        print("warnings:", iss.G_INFO_CONTAINER["warnings"])

    config.RUN = True
    # END
    if not config.RUN:
        print("="*50)
        return

    #################################################
    #                  EMULATING                    #
    #################################################

    emulate(data, DEVICE, actives, built, line_indicator, COMMAND_COUNTER, jump_list)

def double_pass_program_loading():
    print("Loading {}, with consts: {}".format(config.FILE_NAME, config.CONSTS))

    # First loading Pass
    program, line_indicator, jump_list, file_settings, data = loading.load_program(config.FILE_NAME, config.CONSTS)

    # Find CPU profile
    PROFILE_NAME = get_profile_name(file_settings)

    # GET PROFILE AND DEVICE
    CPU_PROFILE, COMMAND_COUNTER, DEVICE, emulator, CONSTS, KEYWORDS = loading.get_profile(config.DEFAULT_PROFILES_PATH, PROFILE_NAME, config.CONSTS)

    loading.update_keywords(KEYWORDS)
    iss.base.load_profie(CPU_PROFILE, emulator)
    config.setupsettings(parserargs, "settings.ini", None)

    print("Reloading {}, with consts: {}".format(config.FILE_NAME, config.CONSTS))

    # Second loading Pass
    program, line_indicator, jump_list, file_settings, data = loading.load_program(config.FILE_NAME, config.CONSTS)

    actives = loading.find_executable_cores(program)

    
    config.TIME_MILTIPLAYER = 1/float(CPU_PROFILE["CPU"]["parametrs"]["clock_speed"])

    return program, jump_list, file_settings, actives, line_indicator, data, DEVICE, COMMAND_COUNTER

def get_build_telemetry_times(program, time_start, compile_end_time):
    total_command_count = sum([len(x) for x in program.values()])
    TOTAL = (compile_end_time-time_start)/1000000.0
    PER_CMD = 0.0
    if total_command_count != 0:
        PER_CMD = (compile_end_time-time_start)/(total_command_count*1000000.0)
    return total_command_count, TOTAL, PER_CMD

def emulate(data, DEVICE, actives, built, line_indicator, COMMAND_COUNTER, jump_list):
    time_start = time.thread_time_ns()
    def end_sequence():
        time_end = time.thread_time_ns()
        
        TOTAL = (time_end-time_start)/1000000000.0
        PER_CMD = (time_end-time_start)/(COMMAND_COUNTER[core_id]*1000000) if COMMAND_COUNTER[core_id] != 0 else 0.0

        print("="*50)
        print("Core {} finished work ({} ticks, apr. {:0.3f}s on device)".format(core_id, COMMAND_COUNTER[core_id], COMMAND_COUNTER[core_id]*config.TIME_MILTIPLAYER))
        print("Total execution time: {:0.3f}s, {:0.3f} ms per command".format(TOTAL, PER_CMD))
        actives.remove(active)

    if config.USE_DATA_BLOCKS:
        for adress, value in data.items():
            try:
                DEVICE.RAM[adress] = value
            except Exception as err:
                raise error.LoadError("Error while parsing data to device: {}".format(err))
    
    # MAIN LOOP
    while True:
        for active in actives:
            core_id = loading.CORE_ID_MAP[active]
            info = dict()

            # GET AND EXECUTE COMMAND            
            try:
                CPU_COMMAND = built[active][DEVICE.get_rom_adress(core_id)]
                PROCESSED_LINE = line_indicator[active][DEVICE.get_rom_adress(core_id)]
            except IndexError:
                end_sequence()
                continue

            if type(CPU_COMMAND) is list:
                for thread, (_type, formed_command, args) in enumerate(CPU_COMMAND):
                    info = iss.execute(_type, formed_command, DEVICE, core_id, args, thread, jump_list[active])
                if iss.LOG_COMMAND_MODE and not iss.FORCE_COMMANDS_IN_SEPERATE_ROWS:
                    print()
            else: 
                _type, formed_command, args = CPU_COMMAND
                info = iss.execute(_type, formed_command, DEVICE, core_id, args, None, jump_list[active])

            # CHECK INFO AND WARNINGS
            if (config.LOG_INFOO == "warnings" or config.LOG_INFOO == "both") and len(info["info"]) > 0:
                print("info:", info["info"])
            if (config.LOG_INFOO == "errors" or config.LOG_INFOO == "both") and len(info["warnings"]) > 0:
                print("warnings:", info["warnings"])

            # CHECK PERFORMANCE
            if not info["skip"]:
                try:
                    COMMAND_COUNTER[core_id] += iss.base.PROFILE.COMMANDSETFULL[CPU_COMMAND[1]]['command_cost']
                except KeyError:
                    COMMAND_COUNTER[core_id] += 1
            DEVICE.end_tick(core_id)

            # STOP FLAG
            if info["stop"]:
                end_sequence()

        # END CPU TICK
        DEVICE.end_cpu_tick()
        if config.SPEED != -1:
            time.sleep(1/config.SPEED)

        # Break loop
        if len(actives) == 0:
            print("All cores did their duty.")
            break

def save(JUMPLIST, built, compiled):
    to_save = None
    if config.SAVE == "dec": 
        to_save = iss.get_dec(compiled)
    elif config.SAVE == "raw":
        to_save = iss.get_raw(compiled)
    elif config.SAVE == "bin": 
        to_save = iss.get_bin(compiled)
    elif config.SAVE == "py":
        py_to_save = dict()
        for core in loading.KEYWORDS:
            py_to_save[core] = '\n'.join([str(line) for line in compiled[core]])
        loading.save(config.OUTPUT_FILE, py_to_save)
        return
    if config.COMMENTS and to_save is not None:
        to_save = iss.add_comments(to_save, built, JUMPLIST)
    loading.save(config.OUTPUT_FILE, to_save)

def get_profile_name(Settings):
    if config.PROFILE_NAME is None and "PROFILE" in Settings:
        return Settings["PROFILE"]
    raise error.LoadError("Please parse profile for cpu.")
    
if __name__ == "__main__":
    if config.CPYTHON_PROFILING:
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