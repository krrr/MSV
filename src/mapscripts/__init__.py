from .cavern_upper_path import CupMacroController
from .deep_cavern_lower_path1 import Dclp1MacroController
from .deep_cavern_lower_path1_alt import Dclp1MacroControllerAlt
from .void_current3 import Vc3MacroController
from .t_boys_research_train1 import TBoyResearchTrain1


map_scripts = {
    'cup': CupMacroController,
    'dclp1_shiki': Dclp1MacroController,
    'dclp1_exorcist': Dclp1MacroControllerAlt,
    'vc3': Vc3MacroController,
    'tboy_train1': TBoyResearchTrain1
}

map2platform = {
    'cup': 'cavern_upper_path',
    'dclp1_shiki': 'deep_cavern_lower_path1',
    'dclp1_exorcist': 'deep_cavern_lower_path1',
    'vc3': 'void_current3',
    'tboy_train1': 't_boys_research_train1'
}
