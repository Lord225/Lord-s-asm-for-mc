import core.config as config
import core
import argparse

DEBUG_MODE = False

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description='Universal Assembly compiler/debugger for minecraft. Help on wiki: https://github.com/Lord225/Lord-s-asm-for-mc')

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

ACTION_ON_ERROR = None if DEBUG_MODE else 'abort' #'interupt'
ACTION_ON_ERROR = ACTION_ON_ERROR if parserargs.onerror is None else parserargs.onerror


if DEBUG_MODE:
    parserargs.run = True
    parserargs.save = "bin"
    parserargs.comments = True

config.override_from_dict(vars(parserargs))

def main():
    pipeline = core.pipeline.make_preproces_pipeline()

    start_file = config.file

    output, context = core.pipeline.exec_pipeline(pipeline, start_file)

    if 'profile' in context:
        config.override_from_dict(profile=context['profile'])
    if 'init' in context:
        config.override_from_file(context['init'])
    
    output, context = core.pipeline.exec_pipeline(pipeline, start_file)
    

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
                    #TODO HANDLE ERRORS!
                    print(err)

                
                if ACTION_ON_ERROR == "interupt":
                    input()
                elif ACTION_ON_ERROR == "abort":
                    pass
