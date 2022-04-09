import core.error as error
import core.config as config

from core.profile.profile import Profile

def find_key_by_value(dict: dict, value):
    output = []
    for key, val in dict.items():
        if val == value:
            output.append(key)
    return output

def generate_comment(command):
    return command.line

def get_line_labels(labels, index):
    founded_labels = find_key_by_value(labels, index)
    if len(founded_labels) == 0:
        return ''
    
    return f"({','.join(founded_labels)})"
    

def add_comments(program, context):
    if not config.comments or not context['tabulate']:
        return program, context
    profile: Profile = context['profile']
    layouts = profile.arguments
    labels = context['chunk_adreses']

    for _, program_lines in program.items():
        if len(program_lines)==0:
            continue
        longest_layout = len(max(program_lines, key=lambda x: len(x.formatted)).formatted)
        for i, line in enumerate(program_lines):

            formatted_lenght_diffrence = longest_layout-len(line.formatted) 

            line.formatted.extend(['']*formatted_lenght_diffrence)
            line.formatted.append(generate_comment(line))
            line.formatted.append(get_line_labels(labels, i+1))
            if config.show_adresses:
                line.formatted.append(line.physical_adress if 'physical_adress' in line else "None")
            if config.save_comments_after_lines:
                line.formatted.append(line.comment if line.has_key("comment") else "")

    return program, context