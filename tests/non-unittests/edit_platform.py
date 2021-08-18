import pickle
import terrain_analyzer

p = 'mapscripts/eastern_cave_path2.platform'
with open(p, 'rb') as f:
    data = pickle.load(f)

print(data)
with open(p, 'wb') as f:
    pickle.dump(data, f)

