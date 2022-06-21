import core
from core.context import Context
import core.error as error
import core.config as config
from core.profile.profile import Profile

def fill_empty_addresses(program, context: Context):
    profile: Profile = context.get_profile()    
    addresing = profile.adressing

    fill = "0" * addresing.bin_len


    return program, context