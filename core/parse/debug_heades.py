
def find_closest_command(program, debug_command):
    distances = [(i, program_line.line_index_in_file-debug_command.line_index_in_file) for i, program_line in enumerate(program)]
    best = min(distances, key = lambda x: abs(x[1]))
    return best
        

def add_debug_metadata(program, context):
    debug = context['debug']
    for debug_command in debug:
        index, distance = find_closest_command(program, debug_command)
        best_command = program[index]
        if distance < 0:
            best_command.debug = {'post': debug_command}
        else:
            best_command.debug = {'pre': debug_command}
        
            
    return program, context