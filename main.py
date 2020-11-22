#Public domain, free to use, by M. Złotorowicz aka Lord255
VERSION = "0.7"

import math as m
import random as rnd
import core.loading as loading
import core.interpreter_synax_solver as iss
import core.error as error
import argparse
import os
import time
import config

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

# -f -a -o -l -i -e -of -s --const --onefile
parser.add_argument("-f", "--file", type=str, default="Program.lor",  #TODO FIX WITH RELATIVE DIR
help="""Name of file to proces
Default: Program.lor
""")
parser.add_argument("-a", "--action", choices=["build", "compile-dec", "compile-csv", "compile-bin", "compile-py" , "refactor", "interprate"], type=str, default="compile-csv",
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
parser.add_argument("-p",'--profile', type=str, default=None,
help="""Parse CPU profile""")
parser.add_argument("-o", "--outfile", type=str, default="compiled.txt", help="Name of binary to save")
parser.add_argument("-l", "--logmode", choices=["short", "long","None"], type=str, default=None,
help="""Choose method of logging CPU's command while executing
> short - Simple logging
> long  - Full logging
> None  - No logging
Default: None
""")
parser.add_argument("-i", "--info", choices=["warnings", "errors", "both", "None"], type=str, default=None,
help="""Choose CPU warning level
> warnings  - Warnings only
> errors    - Errors only
> both      - Errors and warnings
> None      - No CPU warnings in console
Default: None
""")
parser.add_argument("-e", "--onerror", choices=["interupt", "abort", "None"], type=str, default=None, 
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
parser.add_argument('--onefile', action='append', 
help="""Saves output from diffrent cores in same file""")
parserargs = parser.parse_args()


PROCESSED_LINE = -1


if config.ACTION == "everything":
    raise error.CurrentlyUnsupported("ACTION->everything")


def main():
    print("CPU Assembly tools for minecraft by M. Złotorowicz aka Lord225. 2020")
    print("")

    def end_sequence():
        time_end = time.thread_time_ns()
        TOTAL = (time_end-time_start)/1000000000.0
        PER_CMD = 0.0
        if COMMAND_COUNTER[core_id] != 0:
            PER_CMD = (time_end-time_start)/(COMMAND_COUNTER[core_id]*1000000)
        print("="*50)
        print("Core {} finished work ({} ticks, apr. {}s on device)".format(core_id, COMMAND_COUNTER[core_id], COMMAND_COUNTER[core_id]*config.TIME_MILTIPLAYER))
        print("Total execution time: {:0.4f}s, {:0.3f} ms per command".format(PER_CMD, PER_CMD))
        actives.remove(active)

    #################################################
    #                     LOADING                   #
    #################################################

    load_start_time = time.thread_time_ns()
    print("Loading {}, with consts: {}".format(config.FILE_NAME, config.CONSTS))

    Program, line_indicator, JUMPLIST, Settings, data = loading.load_program(config.FILE_NAME, config.CONSTS) #first pass
    
    #Find CPU profile
    if config.PROFILE_NAME is None and "PROFILE" in Settings:
        PROFILE_NAME = Settings["PROFILE"]
    if PROFILE_NAME is None:
        raise error.LoadError("Please parse profile for cpu.")
    
    #GET PROFILE AND DEVICE
    CPU_PROFILE, COMMAND_COUNTER, DEVICE, emulator, CONSTS, KEYWORDS = loading.get_profile(config.DEFAULT_PROFILES_PATH, PROFILE_NAME, config.CONSTS)
    loading.update_keywords(KEYWORDS)

    print("Reloading {}, with consts: {}".format(config.FILE_NAME, config.CONSTS))
    
    #reload with extended consts.
    Program, line_indicator, JUMPLIST, Settings, data = loading.load_program(config.FILE_NAME, config.CONSTS) #second pass

    actives = loading.find_executable_cores(Program)
    
    #parse arguments
    config.setupsettings(parserargs, "settings.config", None)
    
    if config.ACTION == "interprete":
        print("WARNING: 'interprete' functionality is now deprecated. Do not use it.")

    #################################################
    #                   COMPILING                   #
    #################################################
    
    if config.SHOW_RAW_PROGRAM:
        print("Program:", Program, "\n\nJUMPLIST:", JUMPLIST, "\n\nSettings:", Settings, "\n\nActives Cores:", actives)

    time_start = time.thread_time_ns()

    print("Total load time: {}ms".format((time_start-load_start_time)/1000000))

    if config.ACTION in ["build", "compile-dec", "compile-csv", "compile-bin", "compile-py", "refactor"]:
        #compile
        builded = iss.build_program(Program, line_indicator, JUMPLIST, Settings)
        if config.ACTION[:len("compile")] == "compile":
            to_save = iss.get_compiled(builded, config.BUILD_OFFSET)
        elif config.ACTION == "refactor":
            to_save = iss.form_full_log_command_batch(builded, config.BUILD_OFFSET)

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
        
        if config.ACTION == "compile-dec": 
            to_save = iss.get_dec(to_save)
            loading.save(config.OUTPUT_FILE, to_save)
        elif config.ACTION == "compile-csv":
            to_save = iss.get_csv(to_save)
            loading.save(config.OUTPUT_FILE, to_save, with_decorators = False)
        elif config.ACTION == "compile-bin": 
            to_save = iss.get_bin(to_save)
            loading.save(config.OUTPUT_FILE, to_save)
        elif config. ACTION == "refactor":
            loading.save(config.OUTPUT_FILE, to_save)
        
        #CHECK INFO AND WARNINGS
        if (config.LOG_INFOO == "warnings" or config.LOG_INFOO == "both") and len(iss.G_INFO_CONTAINER["info"]) > 0:
            print("info:", iss.G_INFO_CONTAINER["info"])
        if (config.LOG_INFOO == "errors" or config.LOG_INFOO == "both") and len(iss.G_INFO_CONTAINER["warnings"]) > 0:
            print("warnings:", iss.G_INFO_CONTAINER["warnings"])

        #end
        if config.ACTION != "build":
            print("="*50)
            return


    #################################################
    #                  EMULATING                    #
    #################################################

    if config.USE_DATA_BLOCKS:
        for adress, value in data.items():
            try:
                DEVICE.RAM[adress] = value
            except Exception as err:
                raise error.LoadError("Error while parsing data to device: {}".format(err))
    while True:
        for active in actives:
            core_id = loading.CORE_ID_MAP[active]
            
            #GET AND EXECUTE COMMAND            
            if config.ACTION == "build":
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
            if (config.LOG_INFOO == "warnings" or config.LOG_INFOO == "both") and len(info["info"]) > 0:
                print("info:", info["info"])
            if (config.LOG_INFOO == "errors" or config.LOG_INFOO == "both") and len(info["warnings"]) > 0:
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
        if config.SPEED != -1:
            time.sleep(1/config.SPEED)

        
        if len(actives) == 0:
            print("All cores did their duty.")
            #exit
            break
    
if __name__ == "__main__":
    if config.CPYTHON_PROFILING:
        import cProfile
        cProfile.run("main()", sort="cumtime")
    else:
        if config.ACTION_ON_ERROR is None:
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
                
                if config.ACTION_ON_ERROR == "interupt":
                    input()
                elif config.ACTION_ON_ERROR == "abort":
                    pass