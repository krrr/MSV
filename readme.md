# MSV-Kanna-Ver: OpenCV based MapleStory automation on Python3
Kanna class version of original MS-Visionify (https://github.com/Dashadower/MS-Visionify) 


### *How does it work?*
 It's actually very simple. The bot uses image processing to extract player coordinates from the on-screen minimap. On
 the regular version, it maintains a tree structure of the platforms, selecting a destination platform based on least-visited-first
 strategy. On Version 2, it will use A* to construct a path. After that, it's just a matter of using skills at the right intervals.


### Note of regard to code users
* GPLv3 Licence (same as original project)
* Commercial uses are prohibited
