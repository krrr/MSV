import time
from msv.macro_script import MacroController


class TBoyResearchTrain1(MacroController):
    def __init__(self, conn, config):
        super().__init__(conn, config)
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
        if not self.elite_boss_detected and time.time() - self.last_pickup_money_time > self.pickup_money_interval:
            self.navigate_to_platform('257d1219')  # center top
            self.pickup_money()
            self.last_pickup_money_time = time.time()
            return

        if self.current_platform_hash == '257d1219':  # center right
            self.player_manager.shiki_exo_shiki(128)
        elif self.current_platform_hash == '1b6295e0':  # bottom
            self.player_manager.shikigami_haunting_sweep_move(128)
            self.player_manager.teleport_up()
        else:
            self.navigate_to_platform('257d1219')  # center right

        ### Other buffs
        self.buff_skills(yuki=False)

        # Finished
        return 0

    def pickup_money(self):
        # assume at center right now
        self.logger.info('pick up money')

        self.navigate_to_platform('48acf160')  # top right
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['48acf160'].start_x + 3)
        self.update()
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['48acf160'].end_x + 3)
        self.poll_conn()
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['374d7c30'].start_x + 3)
        time.sleep(0.35)
        self.player_manager.exorcist_charm()
        self.poll_conn()
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['374d7c30'].end_x - 3)  # right middle
        self.poll_conn()

        self.update()
        # Quick other player sound notify
        if self.screen_processor.find_other_player_marker():
            self.alert_sound(2)

        self.navigate_to_platform('1b6295e0')  # ensure at bottom

        self._place_set_skill('yaksha_boss')

        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['8e08385f'].start_x + 3)  # left middle
        self.update()
        self.navigate_to_platform('8e08385f')

        self.poll_conn()
        self.update()
        self.navigate_to_platform('c26c0f47')
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['c26c0f47'].end_x - 4)