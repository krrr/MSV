import time
import math
import random
from msv.macro_script import MacroController
from msv.util import random_number
from msv.screen_processor import MiniMapError
import msv.directinput_constants as dc


class TrainNoDest2(MacroController):
    def __init__(self, conn=None, config=None):
        super().__init__(conn, config)
        self.aoe_skills = ['erda_shower', 'true_arachnid_reflection', 'worldreaver', 'solar_crest', 'rising_rage']

    def loop(self):
        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        if self.current_platform_hash == '871a8635':  # bottom
            self.buff_skills()
            if self.player_manager.is_skill_usable('burning_soul_blade'):
                self.player_manager.burning_soul_blade(set=False)

            self.dbl_jump_atk(self.terrain_analyzer.platforms['871a8635'].end_x - 6)
            self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['def767b6'].end_x - 5)  # rope x
            self.navigate_to_platform('def767b6')
            self.dbl_jump_atk(self.terrain_analyzer.platforms['871a8635'].start_x + 1)
            time.sleep(1.25 + random_number(0.05))
        else:
            self.player_manager.dbl_jump_move(self.terrain_analyzer.platforms['871a8635'].start_x+1, attack=True)
            self.update()
            self.navigate_to_platform('871a8635')  # bottom

        # Finished
        return 0

    def dbl_jump_atk(self, goal_x):
        self.player_manager.update()
        loc_delta = self.player_manager.x - goal_x
        if abs(loc_delta) < self.player_manager.horizontal_goal_offset:
            return True

        self.keyhandler.single_press(dc.DIK_LEFT if loc_delta > 0 else dc.DIK_RIGHT)  # turn to correct direction

        start_time = time.time()
        time_limit = math.ceil(abs(loc_delta) / self.player_manager.x_movement_enforce_rate) + 3

        cnt = 0
        target_cnt = random.randint(1, 2)
        while True:
            dis = abs(self.player_manager.x - goal_x)
            if dis <= self.player_manager.horizontal_goal_offset:
                return True

            if dis <= self.player_manager.horizontal_movement_threshold:
                self.player_manager.horizontal_move_goal(goal_x)
            else:
                if loc_delta > 0:
                    self.player_manager.dbl_jump_left(attack=True)
                else:
                    self.player_manager.dbl_jump_right(attack=True)

            if cnt == target_cnt:
                self.use_random_aoe()
                target_cnt = 9999

            try:
                self.update()
            except MiniMapError:
                if self.player_manager.in_bild_pos():
                    pass
                else:
                    raise

            if time.time() - start_time > time_limit:
                return False

            cnt += 1

    def use_random_aoe(self):
        random.shuffle(self.aoe_skills)
        for i in self.aoe_skills:
            if not self.player_manager.is_skill_usable(i):
                continue
            time.sleep(0.08 + random_number(0.02))
            self.logger.debug('use aoe ' + i)
            if i == 'erda_shower' and not self.current_platform_hash == '871a8635':  # avoid down to rope
                continue
            if i == 'true_arachnid_reflection' or i == 'erda_shower':
                self.player_manager.use_set_skill(i)
            else:
                getattr(self.player_manager, i)()
            break
