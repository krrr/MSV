import msv.macro_script, time
# time.sleep(2)

macro = msv.macro_script.MacroController()
macro.terrain_analyzer.load("../../msv/resources/platform/labyrinth_interior1.platform")
macro.terrain_analyzer.generate_solution_dict()

macro.update()
# macro.navigate_to_platform('8ff668b3')
# macro.player_manager.showdown()

# while True:
#     data = macro.loop()
#     print(data)
