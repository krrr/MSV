import time
from macro_script import MacroController
import directinput_constants as dc


class TBoyResearchTrain1(MacroController):
    def __init__(self, keymap, logger_queue, cmd_queue):
        super().__init__(keymap=keymap, log_queue=logger_queue, cmd_queue=cmd_queue)
        self.last_pickup_money_time = time.time() + 20

    def loop(self):
        ret = self._loop_common_job()
        if ret != 0:
            return ret

        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        # set skills
        if not self.elite_boss_detected and self.set_skills(combine=True):
            return

        # pickup money
        if not self.elite_boss_detected and time.time() - self.last_pickup_money_time > self.pickup_money_interval:
            self.navigate_to_platform('257d1219')  # center top
            self.pickup_money()
            self.last_pickup_money_time = time.time()
            return

        if self.current_platform_hash == '257d1219':  # center right
            if not (126 <= self.player_manager.x <= 130):
                self.player_manager.horizontal_move_goal(128)

            dir_ = dc.DIK_RIGHT if self.player_manager.x < 128 else dc.DIK_LEFT
            self.keyhandler.single_press(dir_)
            self.player_manager.shikigami_haunting()
            time.sleep(0.05)
            self.player_manager.exorcist_charm(False)
            self.player_manager.stay(128, 1.23 + abs(self.player_manager.random_duration(0.04)))
            self.keyhandler.single_press(dc.DIK_LEFT if dir == dc.DIK_RIGHT else dc.DIK_LEFT)
            self.player_manager.shikigami_haunting()
            self.player_manager.stay(128, 1.23 + abs(self.player_manager.random_duration(0.04)))
        elif self.current_platform_hash == '1b6295e0':  # bottom
            self.player_manager.shikigami_haunting_sweep_move(127)
            self.player_manager.teleport_up()
        else:
            self.navigate_to_platform('257d1219')  # center right

        ### Other buffs
        self.buff_skills(yuki=False)
        time.sleep(0.05)

        # Finished
        self.loop_count += 1
        return 0

    def pickup_money(self):
        # assume at center right now
        self.logger.info('pick up money')

        self.navigate_to_platform('48acf160')  # top right
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['48acf160'].start_x + 3)
        self.update()
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['48acf160'].end_x + 3)
        self.check_cmd_queue()
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['374d7c30'].start_x + 3)
        time.sleep(0.35)
        self.player_manager.exorcist_charm()
        self.check_cmd_queue()
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['374d7c30'].end_x - 3)  # right middle
        self.check_cmd_queue()

        self.update()
        # Quick other player sound notify
        if self.screen_processor.find_other_player_marker():
            self.alert_sound()

        self.navigate_to_platform('1b6295e0')  # ensure at bottom

        self._place_set_skill('yaksha_boss')

        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['8e08385f'].start_x + 3)  # left middle
        self.update()
        self.navigate_to_platform('8e08385f')

        self.check_cmd_queue()
        self.update()
        self.navigate_to_platform('c26c0f47')
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['c26c0f47'].end_x - 4)