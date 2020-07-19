import src.macro_script, time
# time.sleep(2)

macro = src.macro_script.MacroController(rune_model_dir='../../src/arrow_classifier_keras_gray.h5')
macro.terrain_analyzer.load("../unittest_data/mirror_touched_sea2.platform")
macro.terrain_analyzer.generate_solution_dict()

macro.player_manager.update()
macro.current_platform_hash = '6029314b'
macro.navigate_to_platform('0f9c84c4')

# while True:
#     data = macro.loop()
#     print(data)
