import logging
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
    def override(self, other: 'SectionMeta'):
        if self.name != other.name:
            raise
        if other.offset is not None:
            self.offset = other.offset
        if other.write is not None:
            self.write = other.write

    def __repr__(self):
        return f"SectionMeta({self.name}, {self.offset}, {self.write})"
    
    def __dict__(self):
        return {'name': self.name, 'offset': self.offset, 'write': self.write}



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
            logging.debug(f"Matched label in line {line_obj}: {label}")
            if 'label' not in label:
                raise error.ParserError(line_obj.line_index_in_file, f"Cannot find label '{label}'")
            if label['label'] in context.labels:
                raise error.ParserError(line_obj.line_index_in_file, f"Label '{label['label']}' is not unique")
            context.labels[label['label']] = len(output)+1
        else:
            output.append(line_obj)
    return output, context


def check_section_exists(context: Context):
    profilekeywords = set(context.get_profile().entrypoints)
    entrykeywords = set(context.sections)
    
    missing_entrypoints = profilekeywords-entrykeywords

    if len(missing_entrypoints) != 0:
        msg = f"Keywords: {missing_entrypoints} are defined in profile but not used" if len(missing_entrypoints) != 1 else  f"Keyword: {missing_entrypoints} is defined in profile but never used"
        if config.rise_on_missing_entrypoint:
            raise error.ParserError(None, msg)
        else:
            context.warnings.append(msg)

def find_sections(program, context: Context):
    output = list()
    current_section = SectionMeta('default', 0, 0)
    keysections = {name: SectionMeta(name, val['offset'], val['write']) for name, val in context.get_profile().entrypoints.items()}
    context.sections = {'default': current_section}
    
    for line_obj in program:
        section = check_for_new_section(line_obj)

        if section is not None:
            current_section = section

            if current_section.name in keysections:
                context.sections[current_section.name] = keysections[current_section.name]
                context.sections[current_section.name].override(current_section)
            else:
                context.sections[current_section.name] = current_section
            
                
        else:
            output.append(line_obj)

        line_obj.section = current_section
    
    check_section_exists(context)
        
    return output, context