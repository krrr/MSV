from .cavern_upper_path import CupMacroController
from .deep_cavern_lower_path1 import Dclp1MacroController
from .deep_cavern_lower_path1_alt import Dclp1MacroControllerAlt
from .t_boys_research_train1 import TBoyResearchTrain1
from .bash_club3 import BashClub3
from .fox_tree_top_path import FoxTreeTopPath
from .fox_tree_lower_path3 import FoxTreeLowerPath3
from .corridor_h01 import CorridorH01
from .first_drill_hall import FirstDrillHall
from .final_edge_of_light4 import Fel4MacroController
from .kerning_tower_2f_cafe4 import KerningTower2FCafe4
from .kerning_tower_5f_shops4 import KerningTower5FShops4
from .kerning_tower_b1_store2 import KerningTowerB1Store2
from .labyrinth_interior1 import LabyrinthInterior1
from .eastern_cave_path2 import EasternCavePath2
from .end_of_the_world1_4 import EndOfTheWorld1_4


map_scripts = {
    'cup': CupMacroController,
    'dclp1_shiki': Dclp1MacroController,
    'dclp1_exorcist': Dclp1MacroControllerAlt,
    'fel4': Fel4MacroController,
    'interior1': LabyrinthInterior1,
    'End of the World 1-4': EndOfTheWorld1_4,
    'tboy_train1': TBoyResearchTrain1,
    'b1_store2': KerningTowerB1Store2,
    '2f_cafe4': KerningTower2FCafe4,
    '5f_shops4': KerningTower5FShops4,
    'first_drill_hall': FirstDrillHall,
    'corridor_h01': CorridorH01,
    'bash_club3': BashClub3,
    'fox_tree_top_path': FoxTreeTopPath,
    'fox_tree_lower_path3': FoxTreeLowerPath3,
    'ecp2': EasternCavePath2,
}

map2platform = {
    'cup': 'cavern_upper_path',
    'dclp1_shiki': 'deep_cavern_lower_path1',
    'dclp1_exorcist': 'deep_cavern_lower_path1',
    'fel4': 'final_edge_of_light4',
    'interior1': 'labyrinth_interior1',
    'End of the World 1-4': 'end_of_the_world1_4',
    'tboy_train1': 't_boys_research_train1',
    'b1_store2': 'kerning_tower_b1_store2',
    '2f_cafe4': 'kerning_tower_2f_cafe4',
    '5f_shops4': 'kerning_tower_5f_shops4',
    'first_drill_hall': 'first_drill_hall',
    'corridor_h01': 'corridor_h01',
    'bash_club3': 'bash_club3',
    'fox_tree_top_path': 'fox_tree_top_path',
    'fox_tree_lower_path3': 'fox_tree_lower_path3',
    'ecp2': 'eastern_cave_path2',
}
