try:
    import core
except ModuleNotFoundError as module:
    print(f"{module} You can install dependencies by running:\n\t pip install -r requirements.txt")
    exit()

from types import ModuleType
import argparse
import core.error as error
import core.config as config

DEBUG_MODE = False

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
parser.add_argument("-s", "--save", choices=["dec", "bin", "py", "raw", "pad", "schem"], type=str, default = None,
help="""> dec - Build source and save in easy-to-read format
> pad - Build source and save as binary with padding to bytes
> bin - Build source and save as binary with padding to arguments
> py  - Build source and save as python dict
> raw - Build source and save as decimal representation of bytes
> schem - Build source and save as schematic
Default: None (will not save)""")

parser.add_argument('-c','--comments', dest='comments', action='store_true', help="Add debug information on the end of every line in output files")
parser.set_defaults(feature=False)

parser.add_argument('-r', '--run', dest='run', action='store_true', help="Run emulation after compilation")
parser.set_defaults(feature=False)

parser.add_argument('--logs', dest='logmode', action='store_true', help="Show emulator's disassebly")
parser.set_defaults(feature=False)

parser.add_argument('--why', dest='why_error', action='store_true', help="Program will try harder to find why command cannot be mached")
parser.set_defaults(feature=False)

parserargs = parser.parse_args()

def show_warnings(context):
    for warning in context['warnings']:
        print(f"Warning: {warning}")
def show_outfiles(context):
    print("Output files:")
    SPACE = " "*4
    for chunk, filename in context['outfiles'].items():
        print(SPACE, chunk, filename)
def override_debug():
    if DEBUG_MODE:
        config.override_from_dict(
            run = False,
            save = "schem",
            comments = True,
            onerror = 'None',
            debug = True,
            logmode = True,
            why_error=True)

if config.init is not None:
    config.override_from_file(config.init)
config.override_from_dict(vars(parserargs))
override_debug()

def main():
    print(f"Lord's Compiler Redux is working on '{config.input}'")

    load_preproces_pipeline = core.pipeline.make_preproces_pipeline() # Load & Preprocess
    parse_pipeline = core.pipeline.make_parser_pipeline()             # Parse & Extract arguments
    save_pipeline = core.pipeline.make_save_pipeline()                # Format & Save
    format_pipeline = core.pipeline.make_format_pipeline()            # Format
    
    start_file = config.input

    # First pass, loads settings and profiles into context
    output, context = core.pipeline.exec_pipeline(load_preproces_pipeline, start_file, progress_bar_name='Loading')
    if config.show_warnings:
        show_warnings(context)

    # Update configs
    if 'profile_name' in context:
        config.override_from_dict(profile=context['profile_name'])
    if config.init is not None:
        config.override_from_file(config.init)
    if 'init' in context:
        config.override_from_file(context['init'])
    config.override_from_dict(vars(parserargs))
    override_debug()
    
    # Second pass reloads file with new settings
    output, context = core.pipeline.exec_pipeline(load_preproces_pipeline, start_file, {}, progress_bar_name='Reloading')
    if config.show_warnings:
        show_warnings(context)

    # Load profile and pass it to context
    profile = core.profile.profile.load_profile_from_file(context['profile_name'], True)
    context['profile'] = profile

    # Process data using ouput from second pass.
    output, context = core.pipeline.exec_pipeline(parse_pipeline, output, context,  progress_bar_name='Parsing')
    if config.show_warnings:
        show_warnings(context)

    # Compile and Save
    if config.save in ['bin', 'py', 'dec', 'raw', 'pad', "schem"]:
        if config.save == 'schem':
            config.override_from_dict(comments = 'False')
        output, context = core.pipeline.exec_pipeline(save_pipeline, output, context, progress_bar_name='Saving')
        if config.show_warnings:
            show_warnings(context)
        print()
        show_outfiles(context)

    # Emulation
    if config.run:
        if context['profile'].emul is None:
            print("Emulation is not avalible")
            return
        if isinstance(context['profile'].emul, dict):
            core.emulator.custom_emulator.emulate(output, context)
            return
        if isinstance(context['profile'].emul, ModuleType):
            config.override_from_dict(save = 'raw', comments = 'False')
            output, context = core.pipeline.exec_pipeline(format_pipeline, output, context, progress_bar_name='Evaluating')
            core.emulator.emulate(output, context)
            return


    if config.run is False and config.save is None:
        print("Type: \n\tpython compile.py --help \n\nto display help. \n\nExample use:\n * python compile.py --save pad --comments\n * python compile.py --run --logs\n * python compile.py -i src/examples/pm1.lor -o output/sort.schem --save schem")

def on_compilation_error(err: error.CompilerError):
    print("*"*50)
    print(f"Error in line {err.line}:" if err.line is not None else f"Error in unknown line:")
    print(f"{err}")

def on_profile_error(err):
    print("*"*50)
    print('Error loading profile:')
    print(f'{err}')

def other_error(err):
    print("*"*50)
    print('Other compilig error:')
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
            finally:
                if config.onerror == "interupt":
                    input()
                elif config.onerror == "abort":
                    pass