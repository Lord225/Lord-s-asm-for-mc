try:
    import core
except ModuleNotFoundError as module:
    print(f"{module} You can install dependencies by running:\n\t pip install -r requirements.txt")
    exit()

from types import ModuleType
import argparse
import core.error as error
import core.config as config
import core.context as contextlib
import sys
import os

DEBUG_MODE = True

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawTextHelpFormatter, 
    description=
"""Custom assembly Compiler and Emulator. Github: https://github.com/Lord225/Lord-s-asm-for-mc
    
You can start with: \t 'python compile.py --save pad --comments'

It will compile "program.lor" and save it in "output" dir.
if emulation is avalible add --run to emulate compiler program and --logs to show instruction in console.
""")

parser.add_argument("-i", "--input", type=str, default="src/program.lor",
help="""Name of file to compile
Default: src/program.lor""")

parser.add_argument("-o", "--output", type=str, default="output/compiled.txt", help="Name of file to save in")
parser.add_argument("-s", "--save", choices=["bin", "pip", "hex", "pad", "schem"], type=str, default = 'pip',
help="""> pad - Build source and save as binary with padding to bytes
> bin - Build source and save as binary with padding to arguments
> pip - Build source and dump json to stdout (for pipelining)
> hex - Build source and save as hexadecimal representation of bytes
> schem - Build source and save as schematic
Default: pip (will not save)""")

parser.add_argument('-c','--comments', dest='comments', action='store_true', help="Add debug information on the end of every line in output files")
parser.set_defaults(feature=False)

parser.add_argument('-r', '--run', dest='run', action='store_true', help="Run emulation after compilation")
parser.set_defaults(feature=False)

parser.add_argument('--logs', dest='logmode', action='store_true', help="Show emulator's disassebly")
parser.set_defaults(feature=False)

parser.add_argument('--why', dest='why_error', action='store_true', help="Program will try harder to find why command cannot be mached")
parser.set_defaults(feature=False)

parser.add_argument('--reassume', dest='reassume', action='store_true', help="Show informations about profile")
parser.set_defaults(feature=False)

parserargs = parser.parse_args()


def show_warnings(context: contextlib.Context):
    for warning in context.warnings:
        print(f"Warning: {warning}")
    context.warnings.clear()
def show_outfiles(context: contextlib.Context):
    print("Output files:")
    SPACE = " "*4
    if context.outfiles:
        for filename in context.outfiles:
            print(SPACE, filename)
    else:
        print("None")
def override_debug():
    if DEBUG_MODE:
        config.override_from_dict(
            run = True,
            save = "pad",
            comments = True,
            onerror = 'None',
            debug = True,
            logmode = True,
            why_error=True
        )

if config.init is not None:
    config.override_from_file(config.init)
config.override_from_dict(vars(parserargs))
override_debug()


if config.save == "pip":
    # redirect output to void
    if not DEBUG_MODE:
        sys.stdout = open(os.devnull, 'w')

def main():
    
    print(f"Lord's Compiler Redux is working on '{config.input}'")

    load_preproces_pipeline = core.pipeline.make_preproces_pipeline() # Load & Preprocess
    parse_pipeline = core.pipeline.make_parser_pipeline()             # Parse & Extract arguments
    save_pipeline = core.pipeline.make_save_pipeline()                # Format & Save
    format_pipeline = core.pipeline.make_format_pipeline()            # Format
    
    start_file = config.input

    # First pass, loads settings and profiles into context
    output, context = core.pipeline.exec_pipeline(load_preproces_pipeline, start_file, contextlib.Context(None), progress_bar_name='Loading')
    if config.show_warnings:
        show_warnings(context)

    # Update configs
    if context.profile_name:
        config.override_from_dict(profile=context.profile_name)
    if config.init is not None:
        config.override_from_file(config.init)
    if context.init:
        config.override_from_file(context.init)
    config.override_from_dict(vars(parserargs))
    override_debug()

    # Load profile and pass it to context
    profile = core.profile.profile.load_profile_from_file(f"{config.default_json_profile_path}/{context.profile_name}", True)

    # Second pass reloads file with new settings
    output, context = core.pipeline.exec_pipeline(load_preproces_pipeline, start_file, contextlib.Context(profile), progress_bar_name='Reloading')

    if config.show_warnings:
        show_warnings(context)
    
    if config.reassume:
        from core.profile.reasume import reasume
        reasume(context)
        return
        

    # Process data using ouput from second pass.
    output, context = core.pipeline.exec_pipeline(parse_pipeline, output, context, progress_bar_name='Parsing')
    if config.show_warnings:
        show_warnings(context)

    # Compile and Save
    if config.save in ['bin', 'pip', 'hex', 'pad', "schem"]:
        if config.save == 'schem':
            config.override_from_dict(comments = 'False')
        output, context = core.pipeline.exec_pipeline(save_pipeline, output, context, progress_bar_name='Saving')
        if config.show_warnings:
            show_warnings(context)
        print()
        show_outfiles(context)

    # Emulation
    if config.run:
        if context.get_profile().emul is None:
            print("Emulation is not avalible")
            return
        if isinstance(context.get_profile().emul, dict):
            core.emulator.custom_emulator.emulate(output, context)
            return
        if isinstance(context.get_profile().emul, ModuleType):
            config.override_from_dict(save = 'bin', comments = 'False')
            output, context = core.pipeline.exec_pipeline(format_pipeline, output, context, progress_bar_name='Evaluating')
            core.emulator.emulate(output, context)
            return


    if config.run is False and config.save is None:
        print("Type: \n\tpython compile.py --help \n\nto display help. \n\nExample use:\n * python compile.py --save pad --comments\n * python compile.py --run --logs\n * python compile.py -i src/examples/pm1.lor -o output/sort.schem --save schem")

def on_compilation_error(err: error.CompilerError):
    print("*"*50) 
    print(f"Error in line {err.line}:" if err.line is not None else f"Error in unknown line:")
    print(f"{err.info}")

def on_profile_error(err):
    print("*"*50)
    print('Error loading profile:')
    print(f'{err}')

def other_error(err):
    print("*"*50)
    print('Other compile error:')
    print(f'{err}')

def key_error(err):
    print("*"*50)
    print(f"Internal compiler error (missing key): Expected: {err}")


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
            except KeyError as err:
                key_error(err) 
            except Exception as err:
                other_error(err)
            finally:
                if config.onerror == "interupt":
                    input()
                elif config.onerror == "abort":
                    pass
        if DEBUG_MODE:
            print("WARNING: Turn off debug mode before push")