from .cavern_upper_path import CupMacroController
from .deep_cavern_lower_path1 import Dclp1MacroController
from .deep_cavern_lower_path1_alt import Dclp1MacroControllerAlt
from .void_current3 import Vc3MacroController
from .t_boys_research_train1 import TBoyResearchTrain1
from .bash_club3 import BashClub3
from .fox_tree_top_path import FoxTreeTopPath
from .fox_tree_lower_path3 import FoxTreeLowerPath3
from .corridor_h01 import CorridorH01


map_scripts = {
    'cup': CupMacroController,
    'dclp1_shiki': Dclp1MacroController,
    'dclp1_exorcist': Dclp1MacroControllerAlt,
    'vc3': Vc3MacroController,
    'tboy_train1': TBoyResearchTrain1,
    'bash_club3': BashClub3,
    'fox_tree_top_path': FoxTreeTopPath,
    'fox_tree_lower_path3': FoxTreeLowerPath3,
    'corridor_h01': CorridorH01,
}

map2platform = {
    'cup': 'cavern_upper_path',
    'dclp1_shiki': 'deep_cavern_lower_path1',
    'dclp1_exorcist': 'deep_cavern_lower_path1',
    'vc3': 'void_current3',
    'tboy_train1': 't_boys_research_train1',
    'bash_club3': 'bash_club3',
    'fox_tree_top_path': 'fox_tree_top_path',
    'fox_tree_lower_path3': 'fox_tree_lower_path3',
    'corridor_h01': 'corridor_h01',
}
