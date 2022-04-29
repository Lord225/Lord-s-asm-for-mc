import core
import core.error as error
import core.config as config
from core.profile.profile import Profile

def fill_empty_addresses(program, context):
    profile: Profile = context['profile']    
    addresing = profile.adressing

    fill = "0" * addresing.bin_len


    return program, context