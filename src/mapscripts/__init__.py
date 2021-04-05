from .cavern_upper_path import CupMacroController
from .deep_cavern_lower_path1 import Dclp1MacroController
from .deep_cavern_lower_path1_alt import Dclp1MacroControllerAlt
from .void_current3 import Vc3MacroController
from .t_boys_research_train1 import TBoyResearchTrain1
from .bash_club3 import BashClub3
from .fox_tree_top_path import FoxTreeTopPath
from .fox_tree_lower_path3 import FoxTreeLowerPath3
from .corridor_h01 import CorridorH01
from .first_drill_hall import FirstDrillHall
from .final_edge_of_light4 import Fel4MacroController
from .kerning_tower_2f_cafe4 import KerningTower2FCafe4
from .kerning_tower_5f_shops4 import KerningTower5FShops4


map_scripts = {
    'cup': CupMacroController,
    'dclp1_shiki': Dclp1MacroController,
    'dclp1_exorcist': Dclp1MacroControllerAlt,
    'fel4': Fel4MacroController,
    'vc3': Vc3MacroController,
    'tboy_train1': TBoyResearchTrain1,
    '2f_cafe4': KerningTower2FCafe4,
    '5f_shops4': KerningTower5FShops4,
    'first_drill_hall': FirstDrillHall,
    'corridor_h01': CorridorH01,
    'bash_club3': BashClub3,
    'fox_tree_top_path': FoxTreeTopPath,
    'fox_tree_lower_path3': FoxTreeLowerPath3,
}

map2platform = {
    'cup': 'cavern_upper_path',
    'dclp1_shiki': 'deep_cavern_lower_path1',
    'dclp1_exorcist': 'deep_cavern_lower_path1',
    'fel4': 'final_edge_of_light4',
    'vc3': 'void_current3',
    'tboy_train1': 't_boys_research_train1',
    '2f_cafe4': 'kerning_tower_2f_cafe4',
    '5f_shops4': 'kerning_tower_5f_shops4',
    'first_drill_hall': 'first_drill_hall',
    'corridor_h01': 'corridor_h01',
    'bash_club3': 'bash_club3',
    'fox_tree_top_path': 'fox_tree_top_path',
    'fox_tree_lower_path3': 'fox_tree_lower_path3',
}
