import core.error as error
import core.config as config
import tabulate

from core.profile.profile import Profile

def generate_comment(command):
    return command.line


def add_comments(program, context):
    if not config.comments and not config.tabulate:
        return program, context
    profile: Profile = context['profile']
    layouts = profile.arguments
    longest_layout = len(max(layouts.values(), key=lambda x: len(x))) # get len of longest layout
    
    for _, program_lines in program.items():
        for line in program_lines:
            line.formatted.extend(['']*(longest_layout-len(line.formatted)))
            line.formatted.append(generate_comment(line))

    return program, context