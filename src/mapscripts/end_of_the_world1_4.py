import time
from macro_script import MacroController
import directinput_constants as dc


# void current 3 script
# noinspection PyPep8Naming
class EndOfTheWorld1_4(MacroController):
    CENTER_X = 77
    LEFT_X = 60
    RIGHT_X = 91

    def __init__(self, keymap, log_queue, cmd_queue, config):
        super().__init__(keymap, log_queue, cmd_queue, config)
        self.last_pickup_money_time = time.time() + 20

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
            self.pickup_money()
            self.last_pickup_money_time = time.time()
            return

        if self.current_platform_hash == '5b53ae83':  # bottom
            if abs(self.player_manager.x - self.CENTER_X) <= 5:
                x = self.player_manager.x
                self.player_manager.horizontal_move_goal(x - 5 if x < self.CENTER_X else x + 5)

            if self.player_manager.x < self.LEFT_X - self.player_manager.TELEPORT_HORIZONTAL_RANGE:
                self.player_manager.shikigami_haunting_sweep_move(self.LEFT_X - self.player_manager.TELEPORT_HORIZONTAL_RANGE + 3)
            elif self.player_manager.x > self.RIGHT_X + self.player_manager.TELEPORT_HORIZONTAL_RANGE:
                self.player_manager.shikigami_haunting_sweep_move(self.RIGHT_X + self.player_manager.TELEPORT_HORIZONTAL_RANGE - 3)

            if self.player_manager.x < self.CENTER_X:
                self.player_manager.jumpr()
                time.sleep(0.05)
                self.player_manager.teleport_right()
            else:
                self.player_manager.jumpl()
                time.sleep(0.05)
                self.player_manager.teleport_left()
        elif self.current_platform_hash == '6865257d':  # the platform
            to_left = self.player_manager.x > self.CENTER_X
            self.keyhandler.single_press(dc.DIK_RIGHT if to_left else dc.DIK_LEFT)
            self.player_manager.shikigami_haunting()
            self.keyhandler.single_press(dc.DIK_LEFT if to_left else dc.DIK_RIGHT)
            self.player_manager.shikigami_haunting(wait_delay=False)
            time.sleep(0.1)
            self.player_manager.teleport_left() if to_left else self.player_manager.teleport_right()
            self.update()
            self.player_manager.horizontal_move_goal(self.LEFT_X+2 if to_left else self.RIGHT_X-9)
        else:
            self.navigate_to_platform('5b53ae83')  # to bottom first

        ### Other buffs
        self.buff_skills(yuki=False)
        time.sleep(0.05)

        # Finished
        self.loop_count += 1
        return 0

    def pickup_money(self):
        self.logger.info('pick up money')
        self.navigate_to_platform('c214856a')  # above the platform
        ### above the platform
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['c214856a'].start_x + 15)
        self.player_manager.stay(1.5 + abs(self.player_manager.random_duration(0.1)))
        self.update()
        self.check_cmd_queue()
        self.navigate_to_platform('5b53ae83')

        self.check_cmd_queue()

        ### bottom
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['5b53ae83'].start_x + 4)
        self.player_manager.stay(0.45 + abs(self.player_manager.random_duration(0.05)))
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['5b53ae83'].end_x - 1)
        self.player_manager.stay(0.3 + abs(self.player_manager.random_duration(0.05)))
        self.navigate_to_platform('b70e34c7')  # center right

        ### center right
        if time.time() - self.player_manager.last_skill_use_time['yaksha_boss'] >= 10:
            self.player_manager.last_skill_use_time['yaksha_boss'] = 0  # force setting yaksha boss
            self._place_set_skill('yaksha_boss')
        else:
            self.player_manager.stay(0.5 + abs(self.player_manager.random_duration(0.05)))
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['6a51d25a'].start_x + 4)
        self.update()
        self.check_cmd_queue()
        self.navigate_to_platform('6a51d25a')

        ### top right
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['6a51d25a'].start_x + 15)
        self.player_manager.stay(1.1 + abs(self.player_manager.random_duration(0.1)))
