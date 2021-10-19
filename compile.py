from core import emulate
import core.config as config
import core.error as error
import core
import argparse


DEBUG_MODE = False

#TODO const adress space vs packed vs

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description='Custom assembly Compiler and Emulator. \n Github: https://github.com/Lord225/Lord-s-asm-for-mc \n\n You can start with: \n\n\t python compile.py --save pad --comments \n\n It will compile "program.lor" and save it in "output" dir.\n if emulation is avalible add --run to emulate compiler program and --logs to show instruction in console.')

parser.add_argument("-i", "--input", type=str, default="src/program.lor",
help="""Name of file to compile
Default: src/program.lor
""")
parser.add_argument("-o", "--output", type=str, default="output/compiled.txt", help="Name of binary to save")
parser.add_argument("-s", "--save", choices=["dec", "bin", "py", "raw", "pad"], type=str, default = None,
help="""
> dec - Build source and save in easy-to-read format
> pad - Build source and save as binary with padding to bytes
> bin - Build source and save as binary with padding to arguments
> py  - Build source and save as python dict
> raw - Build source and save as decimal representation of bytes
Default: None (will not save)
""")
parser.add_argument('-c','--comments', dest='comments', action='store_true')
parser.set_defaults(feature=False)

parser.add_argument('-r', '--run', dest='run', action='store_true')
parser.set_defaults(feature=False)

parser.add_argument('--logs', dest='logmode', action='store_true', help="Choose method of logging CPU's command while executing")
parser.set_defaults(feature=False)

parserargs = parser.parse_args()

if config.init is not None:
    config.override_from_file(config.init)
config.override_from_dict(vars(parserargs))

def override_debug():
    if DEBUG_MODE:
        config.override_from_dict(
            run = True,
            save = "pad",
            comments = True,
            onerror = 'None',
            debug = True,
            logmode = True)
override_debug()

def show_warnings(context):
    for warning in context['warnings']:
        print(f"Warning: {warning}")
        
def main():
    print(f"Lord's Compiler Redux is working on '{config.input}'")

    load_preproces_pipeline = core.pipeline.make_preproces_pipeline()
    parse_pipeline = core.pipeline.make_parser_pipeline()
    save_pipeline = core.pipeline.make_save_pipeline()
    format_pipeline = core.pipeline.make_format_pipeline()
    
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


    # Compile and save
    if config.save in ['bin', 'py', 'dec', 'raw', 'pad']:
        output, context = core.pipeline.exec_pipeline(save_pipeline, output, context, progress_bar_name='Saving')
        if config.show_warnings:
            show_warnings(context)
        print()
        print("Output files:")
        SPACE = " "*4
        for chunk, filename in context['outfiles'].items():
            print(SPACE, chunk, filename)
    # Emulation
    if config.run:
        config.override_from_dict(save = 'raw', comments = 'False')
        output, context = core.pipeline.exec_pipeline(format_pipeline, output, context, progress_bar_name='Evaluating')
        emulate.emulator.emulate(output, context)

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

