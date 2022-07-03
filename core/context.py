from typing import Any, Dict, Optional
from core.error import ProfileLoadError

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import core.profile.profile as profile
    from core.parse.jumps import SectionMeta


class Context:
    def __init__(self, profile: 'Optional[profile.Profile]'):
        if profile is None:
            self.const = dict()
            self.defs = list()
        else:
            # all constant maps in form {'name': 'def'}
            self.const = dict(profile.consts)
            # all definitions in form ['def1', 'def2']
            self.defs = list(profile.defs)

        # loaded profile name. It is temprally to load profile later
        self.profile_name = ''
        # actuall profile class
        self.__profile = profile

        # values written with #data directive in form {address: value}
        self.data = dict() 
        # lines with #debug directive (used for debugger and emulator)
        self.debug = list()
        # definitins of all user defined macros 
        self.macros = dict()
        # warning messages
        self.warnings = list()

        # list of init files
        self.init = list()
        # offset of the schematic saved in the file
        self.schematic_offset = 0

        # list of output files
        self.outfiles = list()

        # flag to use phisical adresses in labels
        self.use_phisical_adresses = False
        # list of labels with phisical adresses
        self.physical_adresses = dict()
        # list of labels with normal addresses (counted in commands)
        self.labels = dict()

        # dict of sections in form {'section_name': SectionMeta}
        self.sections: 'Dict[str, SectionMeta]' = dict()

        # unused
        self.chunk_adreses = dict() 
        self.used_addresses = dict()
        self.namespace = None

    def get_profile(self):
        if self.__profile is None:
            raise ProfileLoadError('Logic Error - Trying to access profile data before initlilize')
        return self.__profile

    def get_addresses(self):
        if self.use_phisical_adresses:
            return self.physical_adresses
        return self.labels