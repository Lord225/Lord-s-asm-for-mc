import core.config as config
from core.context import Context
import core.error as error
import core.parse as parser
import pprint


def reasume(context: Context):
    profile_name = context.profile_name
    profile = context.get_profile()
    
    print(f"Profile: '{profile_name}'")
    print(f"Info: {str(profile.info)}")
    print(f"Defs: {str(profile.defs)}")

    print("Arg lens: ", end='')
    pprint.pprint(profile.arguments_len)
    print("Args: ")
    pprint.pprint(profile.arguments)

    print("COMMANDS: ")
    for i, (_, definitons) in enumerate(profile.commands_definitions.items()):
        print(i, f"{definitons['pattern'].summarize()}")
    lenght = len(profile.commands_definitions.items())
    print("MACROS: ")
    for i, (_, definitons) in enumerate(profile.macro_definitions.items()):
        print(i+lenght, f"{definitons['pattern'].summarize()}")