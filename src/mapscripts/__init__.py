from .cavern_upper_path import CupMacroController
from .deep_cavern_lower_path1 import Dclp1MacroController
from .deep_cavern_lower_path1_alt import Dclp1MacroControllerAlt

map_scripts = {
    'cup': CupMacroController,
    'dclp1_shiki': Dclp1MacroController,
    'dclp1_exorcist': Dclp1MacroControllerAlt
}

map2platform = {
    'cup': 'cavern_upper_path',
    'dclp1_shiki': 'deep_cavern_lower_path1',
    'dclp1_exorcist': 'deep_cavern_lower_path1'
}
