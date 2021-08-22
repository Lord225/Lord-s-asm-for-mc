import inspect
import core.error as error
from typing import *
from abc import ABC, abstractmethod
import dataclasses

class ValidateClass(ABC):
    @abstractmethod
    def validate_value(self, x):
        pass

@dataclasses.dataclass
class ValueRange(ValidateClass):
    min: float
    max: float

    def validate_value(self, x):
        if not (x in range(self.min, self.max+1)):
            raise error.EmulatorError(f'{x} must be in range [{self.min}, {self.max}]')

def check_arguments(func):
    spec = inspect.getfullargspec(func)
    hints = get_type_hints(func, include_extras=True)

    def wrapper(*args, **kwargs):
        for idx, arg_name in enumerate(spec[0]):
            hint = hints.get(arg_name)
            validators = getattr(hint, '__metadata__', None)
            if not validators:
                continue
            for validator in validators:
                validator.validate_value(args[idx])

        return func(*args, **kwargs)

    return wrapper
