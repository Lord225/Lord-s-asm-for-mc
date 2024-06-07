from core.context import Context
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
    

def add_comments(program, context: Context):
    if not config.comments or config.save == 'pip':
        for line in program:
            line.formatted_comments = line.formatted.copy()
        return program, context
    profile: Profile = context.get_profile()
    labels = context.physical_adresses

    longest_layout = len(max(program, key=lambda x: len(x.formatted)).formatted)
    
    for i, line in enumerate(program):

        formatted_lenght_diffrence = longest_layout-len(line.formatted) 

        line.formatted_comments = line.formatted.copy() 

        line.formatted_comments.extend(['']*formatted_lenght_diffrence)
        line.formatted_comments.append(generate_comment(line))
        line.formatted_comments.append(get_line_labels(labels, i+1))
        if config.show_adresses:
            line.formatted_comments.append(str(line.physical_adress) if 'physical_adress' in line else "None")
        if config.save_comments_after_lines:
            line.formatted_comments.append(line.comment if line.has_key("comment") else "")

    return program, context