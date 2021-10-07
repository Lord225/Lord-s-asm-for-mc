
import core.config as config
import core.error as error
import core
import argparse


DEBUG_MODE = True

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

parser.add_argument("-o", "--outfile", type=str, default="compiled/compiled.txt", help="Name of binary to save")

parser.add_argument('--logs', dest='logmode', action='store_true', help="Choose method of logging CPU's command while executing")
parser.set_defaults(feature=False)

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

parserargs = parser.parse_args()

config.override_from_dict(vars(parserargs))

if DEBUG_MODE:
    config.run = True
    config.save = "bin"
    config.comments = True
    config.onerror = 'abort'

def main():
    load_preproces_pipeline = core.pipeline.make_preproces_pipeline()
    parse_pipeline = core.pipeline.make_parser_pipeline()
    
    start_file = config.file

    output, context = core.pipeline.exec_pipeline(load_preproces_pipeline, start_file)

    if 'profile_name' in context:
        config.override_from_dict(profile=context['profile_name'])
    if 'init' in context:
        config.override_from_file(context['init'])
    
    output, context = core.pipeline.exec_pipeline(load_preproces_pipeline, start_file, {})

    profile = core.profile.profile.load_profile_from_file(context['profile_name'], True)
    context['profile'] = profile

    output, context = core.pipeline.exec_pipeline(parse_pipeline, output, context)

def on_compilation_error(err: error.CompilerError):
    print("*"*50)
    print("Error in line {}:".format(err.line))
    print(f"{err}")
    
    if config.onerror == "interupt":
        input()
    elif config.onerror == "abort":
        return
def on_profile_error(err):
    print("*"*50)
    print('Error loading profile:')
    print(f'{err}')
def other_error(err):
    print("*"*50)
    print('Unhandeled compilig error:')
    print(f'{err}')
if __name__ == "__main__":
    if config.CPYTHON_PROFILING:
        import cProfile
        cProfile.run("main()", sort="cumtime")
    else:
        if config.onerror is None:
            main()
        else:
            try:
                main()
            except error.CompilerError as err:
                on_compilation_error(err)
            except error.ProfileLoadError as err:
                on_profile_error(err)
            except Exception as err:
                other_error(err)
