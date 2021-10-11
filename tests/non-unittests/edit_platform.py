import pickle
import terrain_analyzer

p = '../../msv/resources/platform/labyrinth_interior1.platform'
with open(p, 'rb') as f:
    data = pickle.load(f)

print(data)
data['dark_flare_coord'] = (147, 62)
data['nightmare_invite_coord'] = (153, 47)
with open(p, 'wb') as f:
    pickle.dump(data, f)

