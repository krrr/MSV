# MSV: OpenCV based MapleStory macro
Kanna class version of original MS-Visionify (https://github.com/Dashadower/MS-Visionify) 
![kanna](MapleStory-Kanna.png)

### *How does it work?*
 It's actually very simple. The bot uses image processing to extract player coordinates from the on-screen minimap. On
 the regular version, it maintains a tree structure of the platforms, selecting a destination platform based on least-visited-first
 strategy. On Version 2, it will use A* to construct a path. After that, it's just a matter of using skills at the right intervals.


### Note of regard to code users
* GPLv3 Licence (same as original project)
* Commercial uses are prohibited



### Supported maps
#### Meso farm maps
* dclp1: Deep in the Cavern - Lower Path 1
* interior1: Labyrinth of Suffering Interior 1
#### Leech maps
* b1_store2: B1 Store 2 (141-149)
* 2f_cafe4: 2F Cafe 4 (150-160)
* 5f_shops4: 5F Cosmetics Shops 4 (161-164)
* first_drill_hall: First Drill Hall  (165-173)
* corridor_h01: Corridor H01  (174-176)
* bash_club3: Dingy Brawl 'n' Bash Club 3  (177-185)
* fox_tree_top_path: Fox Tree Top Path  (186-189)
* fox_tree_lower_path3: Fox Tree Lower Path 3 (190-200)
