from .royal_library_section2 import RoyalLibrarySection2
from .plunging_depths3 import PlungingDepths3
from .train_no_dest2 import TrainNoDest2

# dict is ordered in py3.7+
map_scripts = {
    'Royal Library Section 2': RoyalLibrarySection2,
    'Plunging Depths 3': PlungingDepths3,
    'Train with No Destination 2': TrainNoDest2,
}

map2platform = {
    'Royal Library Section 2': 'royal_library_section2',
    'Plunging Depths 3': 'plunging_depths3',
    'Train with No Destination 2': 'train_no_dest2',
}
