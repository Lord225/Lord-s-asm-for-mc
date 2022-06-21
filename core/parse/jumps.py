import core.config as config
from core.context import Context
import core.error as error
import core.profile.patterns as patterns
import core.parse.match_expr as match_expr

class SectionMeta:
    find_section = patterns.Pattern(".{label:token}")
    find_section_with_offset = patterns.Pattern(".{label:token} {offset:num}")
    find_section_with_offset_with_outoffset = patterns.Pattern(".{label:token} {offset:num} {write:num}")

    def __init__(self, name, offset, write):
        self.name = name
        self.offset = offset
        self.write = write

def check_for_new_section(line_obj):
    label1 = match_expr.match_expr(SectionMeta.find_section, line_obj, None)
    label2 = match_expr.match_expr(SectionMeta.find_section_with_offset, line_obj, None)
    label3 = match_expr.match_expr(SectionMeta.find_section_with_offset_with_outoffset, line_obj, None)
    
    if label1 is not None:
        return SectionMeta(label1["label"], None, None)
    if label2 is not None:
        return SectionMeta(label2["label"], label2["offset"], None)
    if label3 is not None:
        return SectionMeta(label3["label"], label3["offset"], label3["write"])
    
    return None  

def find_labels(program, context: Context):
    find_labels = patterns.Pattern("{label:token}:")
    context.labels = dict()
    output = list()
    
    for line_obj in program:
        label = match_expr.match_expr(find_labels, line_obj, None)
        if label is not None:
            if 'label' not in label:
                raise error.ParserError(line_obj.line_index_in_file, f"Cannot find label '{label}'")
            if label['label'] in context.labels:
                raise error.ParserError(line_obj.line_index_in_file, f"Label '{label['label']}' is not unique")
            context.labels[label['label']] = len(output)+1
        else:
            output.append(line_obj)
    return output, context

def find_sections(program, context: Context):
    output = list()
    current_section = SectionMeta('default', 0, 0)
    context.sections = {'default': current_section}

    for line_obj in program:
        section = check_for_new_section(line_obj)

        if section is not None:
            current_section = section
            context.sections[current_section.name] = current_section
        else:
            output.append(line_obj)

        line_obj.section = current_section
        
    return output, context