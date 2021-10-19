import core.config as config
import core.error as error
import core.profile.patterns as patterns
import core.parse.match_expr as match_expr

def find_labels(program, context):
    find_labels = patterns.Pattern("{label:any_str}:")
    labels = {}
    output = list()
    for line_obj in program:
        label = match_expr.match_expr(find_labels, line_obj.tokenized, None)
        if label is not None:
            if 'label' not in label:
                raise error.ParserError(f"Cannot find label '{label}'")
            if label['label'] in labels:
                raise error.ParserError(f"Label '{label['label']}' is not unique")
            labels[label['label']] = len(output)+1
        else:
            output.append(line_obj)
    context['labels'] = labels
    return output, context