import random
import time
from msv.util import random_number, is_compiled
from msv.macro_script import MacroController
import msv.directinput_constants as dc


# End of the World 1-4 script
# noinspection PyPep8Naming
class EndOfTheWorld1_4(MacroController):
    CENTER_X = 77
    LEFT_X = 60
    RIGHT_X = 91

    def __init__(self, keymap, conn, config):
        super().__init__(keymap, conn, config)
        self.last_pickup_money_time = time.time() + 20
        self.alt_pattern = not is_compiled()

    def loop(self):
        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        # set skills
        if not self.elite_boss_detected and self.set_skills(combine=True):
            return

        # pickup money
        if (not self.elite_boss_detected and self.current_platform_hash == '6865257d' and
                time.time() - self.last_pickup_money_time > self.pickup_money_interval):
            if self.player_manager.is_skill_usable('true_arachnid_reflection'):
                self.player_manager.use_set_skill('true_arachnid_reflection')
            self.pickup_money()
            self.last_pickup_money_time = time.time()
            return

        if self.current_platform_hash == '5b53ae83':  # bottom
            if abs(self.player_manager.x - self.CENTER_X) <= 5:
                x = self.player_manager.x
                self.player_manager.horizontal_move_goal(x - 5 if x < self.CENTER_X else x + 5)

            if self.player_manager.x < self.LEFT_X - self.player_manager.TELEPORT_HORIZONTAL_RANGE:
                self.player_manager.shikigami_haunting_sweep_move(self.LEFT_X - self.player_manager.TELEPORT_HORIZONTAL_RANGE)
            elif self.player_manager.x > self.RIGHT_X + self.player_manager.TELEPORT_HORIZONTAL_RANGE:
                self.player_manager.shikigami_haunting_sweep_move(self.RIGHT_X + self.player_manager.TELEPORT_HORIZONTAL_RANGE)

            if self.player_manager.x < self.CENTER_X:
                self.player_manager.jump_right(wait=False)
                time.sleep(0.05)
                self.player_manager.teleport_right()
            else:
                self.player_manager.jump_left(wait=False)
                time.sleep(0.05)
                self.player_manager.teleport_left()
        elif self.current_platform_hash == '6865257d':  # the platform
            if self.alt_pattern:
                if not self.LEFT_X <= self.player_manager.x <= self.LEFT_X + 2:
                    self.player_manager.shikigami_haunting_sweep_move(self.LEFT_X)

                left = random.random() < 0.5
                self.wait_monster('ascendion', 'l' if left else 'r', 2)
                self.keyhandler.single_press(dc.DIK_LEFT if left else dc.DIK_RIGHT, 0.04)
                self.player_manager.shikigami_haunting()
                time.sleep(0.1 + random_number(0.05))
                self.wait_monster('ascendion', 'r' if left else 'l', 2)
                self.keyhandler.single_press(dc.DIK_RIGHT if left else dc.DIK_LEFT, 0.04)
                self.player_manager.shikigami_haunting()
                time.sleep(0.2)
            else:
                to_left = self.player_manager.x > self.CENTER_X
                facing_changed = False
                atk = True
                if to_left:  # at right side now
                    if random.random() < 0.4:
                        facing_changed = True
                        time.sleep(random_number(0.15))
                        self.keyhandler.single_press(dc.DIK_LEFT)
                    self.wait_monster('ascendion', 'l', 1.5)
                else:
                    atk = self.screen_processor.check_monster('ascendion', 'r')

                if atk:
                    if not facing_changed:
                        self.keyhandler.single_press(dc.DIK_LEFT if to_left else dc.DIK_RIGHT)
                    self.player_manager.shikigami_haunting(wait_delay=False)
                    time.sleep(0.1 + random_number(0.05, minus=True))
                    self.player_manager.teleport_left() if to_left else self.player_manager.teleport_right()
                    self.update()
                    self.player_manager.horizontal_move_goal(self.LEFT_X+1 if to_left else self.RIGHT_X-9)
                    time.sleep(0.1 + random_number(0.05, minus=True))
                    self.player_manager.shikigami_haunting()
                else:
                    self.player_manager.optimized_horizontal_move(self.RIGHT_X-9)
                    time.sleep(0.1 + random_number(0.1))
        else:
            self.navigate_to_platform('5b53ae83')  # to bottom first

        ### Other buffs
        self.buff_skills(yuki=False)

        # Finished
        return 0

    def pickup_money(self):
        self.logger.info('pick up money')
        self.navigate_to_platform('c214856a')  # above the platform
        ### above the platform
        p = self.terrain_analyzer.platforms['c214856a']
        center = (p.start_x + p.end_x) // 2
        if self.player_manager.x > center:
            if p.end_x - self.player_manager.x <= 4 or self.player_manager.x < p.end_x - 8:
                self.player_manager.horizontal_move_goal(p.end_x - 5)
        else:
            self.player_manager.horizontal_move_goal(p.start_x + 5)
            self.keyhandler.single_press(dc.DIK_RIGHT)
            self.player_manager.shikigami_haunting()
        self.player_manager.stay(1 + random_number(0.1))
        self.player_manager.horizontal_move_goal(p.end_x - 6 if self.player_manager.x < center else p.start_x + 6)
        self.player_manager.stay(1 + random_number(0.1))
        self.update()
        # Quick other player sound notify
        if self.screen_processor.find_other_player_marker():
            self.alert_sound(2)
        self.poll_conn()
        self.navigate_to_platform('5b53ae83')

        self.poll_conn()

        ### bottom
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['5b53ae83'].start_x + 4)
        self.player_manager.stay(0.4 + random_number(0.1))
        self.poll_conn()
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['5b53ae83'].end_x - 1)
        self.player_manager.stay(1 + random_number(0.1))
        self.navigate_to_platform('b70e34c7')  # center right

        ### center right
        if time.time() - self.player_manager.last_skill_use_time['yaksha_boss'] >= 10:
            self.player_manager.last_skill_use_time['yaksha_boss'] = 0  # force setting yaksha boss
            self._place_set_skill('yaksha_boss')
        else:
            self.player_manager.stay(0.5 + random_number(0.1))
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['6a51d25a'].start_x + 4)
        self.update()
        # Quick other player sound notify
        if self.screen_processor.find_other_player_marker():
            self.alert_sound(2)
        self.poll_conn()
        self.navigate_to_platform('6a51d25a')

        ### top right
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['6a51d25a'].start_x + 9)
        self.player_manager.stay(1.7 + random_number(0.1))
        if random.random() >= 0.5:
            self.player_manager.teleport_down()
        else:
            self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['6a51d25a'].start_x + 3)
            self.player_manager.jump_left()
