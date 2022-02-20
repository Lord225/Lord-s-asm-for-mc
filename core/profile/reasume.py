import core.config as config
import core.error as error
import core.parse as parser
import pprint


def reasume(context):
    profile_name = context['profile_name']
    profile = context['profile']
    
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