from operator import sub
import core.error as error
import core.config as config
import core
import subprocess


def emulate(output, context):
    print("Custom emulation pipeline")
    profile: core.profile.profile.Profile = context.profile
    emul = profile.emul
    if not isinstance(emul, dict):
        raise error.ProfileLoadError(f"Expected Dict with emulation settings got: {emul}")

    save_settings = emul["output"]["save"]
    data_settings = emul["output"]["data"]
    emul_cmd = emul["cmd"]
    
    config.override_from_dict(save_settings)
    
    save_pipeline = core.pipeline.make_save_pipeline()
    
    output, context = core.pipeline.exec_pipeline(save_pipeline, output, context, progress_bar_name='Saving Binary')

    process = [emul_cmd]

    print(f"Calling: {' '.join(process)}")
    print("Emulation Output:\n")

    try:
        subprocess.check_call(process)
    except subprocess.CalledProcessError as err:
        raise error.EmulationError(f"Emulation Error: {err}")


