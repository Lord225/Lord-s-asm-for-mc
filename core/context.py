from typing import Any, Dict, Optional
from core.error import ProfileLoadError

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.parse.jumps import SectionMeta


class Context:
    def __init__(self, profile: Optional[Any]):
        if profile is None:
            self.const = dict()
            self.defs = list()
        else:
            self.const = dict(profile.consts)
            self.defs = list(profile.defs)

        self.profile_name = ''
        self.__profile = profile

        self.data = dict()
        self.debug = list()
        self.entry = dict()
        self.macros = dict()
        self.warnings = list()

        self.init = list()
        self.schematic_offset = 0

        self.outfiles = list()

        self.use_phisical_adresses = False
        self.physical_adresses = dict()
        self.labels = dict()

        self.sections: Dict[str, SectionMeta] = dict()

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