from .cavern_upper_path import CupMacroController
from .deep_cavern_lower_path1 import Dclp1MacroController
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
from .end_of_the_world2_4 import EndOfTheWorld2_4
from .tool_kishin import ToolKishin


# dict is ordered in py3.7+
map_scripts = {
    'T-Boy Train 1': TBoyResearchTrain1,
    'Cavern Upper Path': CupMacroController,
    'Deep Cavern Lower Path 1': Dclp1MacroController,
    'Final Edge of Light 4': Fel4MacroController,
    'Interior 1': LabyrinthInterior1,
    'End of World 1-4': EndOfTheWorld1_4,
    'End of World 2-4': EndOfTheWorld2_4,
    'B1 Store 2': KerningTowerB1Store2,
    '2F Cafe 4': KerningTower2FCafe4,
    '5F Shops 4': KerningTower5FShops4,
    'First Drill Hall': FirstDrillHall,
    'Corridor H01': CorridorH01,
    'Bash Club 3': BashClub3,
    'Fox Tree Top Path': FoxTreeTopPath,
    'Fox Tree Lower Path 3': FoxTreeLowerPath3,
    'Eastern Cave Path 2': EasternCavePath2,
    'Kishin': ToolKishin,
}

map2platform = {
    'T-Boy Train 1': 't_boys_research_train1',
    'Cavern Upper Path': 'cavern_upper_path',
    'Deep Cavern Lower Path 1': 'deep_cavern_lower_path1',
    'Final Edge of Light 4': 'final_edge_of_light4',
    'Interior 1': 'labyrinth_interior1',
    'End of World 1-4': 'end_of_the_world1_4',
    'End of World 2-4': 'end_of_the_world2_4',
    'B1 Store 2': 'kerning_tower_b1_store2',
    '2F Cafe 4': 'kerning_tower_2f_cafe4',
    '5F Shops 4': 'kerning_tower_5f_shops4',
    'First Drill Hall': 'first_drill_hall',
    'Corridor H01': 'corridor_h01',
    'Bash Club 3': 'bash_club3',
    'Fox Tree Top Path': 'fox_tree_top_path',
    'Fox Tree Lower Path 3': 'fox_tree_lower_path3',
    'Eastern Cave Path 2': 'eastern_cave_path2',
}
