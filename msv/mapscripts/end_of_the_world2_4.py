import time
from msv.util import random_number
from msv.macro_script import MacroController


# End of the World 2-4 script
# noinspection PyPep8Naming
class EndOfTheWorld2_4(MacroController):
    X = 108

    def __init__(self, conn, config):
        super().__init__(conn, config)
        self.last_pickup_money_time = time.time() + 20

    def loop(self):
        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        # set skills
        if self.set_skills(combine=True):
            if self.loop_count > 1 and self.current_platform_hash == 'e8c6644f':  # pickup money at top
                self.player_manager.optimized_horizontal_move(self.terrain_analyzer.platforms['e8c6644f'].start_x + 5)
                self.player_manager.stay(0.3 + random_number(0.1))
            return

        # pickup money
        if (self.current_platform_hash == 'bcd4711b' and
                time.time() - self.last_pickup_money_time > self.pickup_money_interval):
            if self.player_manager.is_skill_usable('true_arachnid_reflection'):
                self.player_manager.use_set_skill('true_arachnid_reflection')
            self.pickup_money()
            self.last_pickup_money_time = time.time()
            return

        if self.current_platform_hash == 'bcd4711b':  # the platform
            self.player_manager.shiki_exo_shiki(self.X)
            time.sleep(random_number(0.08))
        else:
            self.navigate_to_platform('bcd4711b')

        ### Other buffs
        self.buff_skills(yuki=False)

        # Finished
        return 0

    def pickup_money(self):
        self.logger.info('pick up money')
        self.navigate_to_platform('268ff3c9')  # above center bottom
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['268ff3c9'].end_x-13)
        self.player_manager.shikigami_haunting()
        self.player_manager.stay(0.4 + random_number(0.1))
        self.navigate_to_platform('059285fa')
        ### bottom
        if time.time() - self.player_manager.last_skill_use_time.get('yaksha_boss', 0) >= 10:
            self.player_manager.last_skill_use_time['yaksha_boss'] = 0  # force setting yaksha boss
            self._place_set_skill('yaksha_boss')
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['059285fa'].start_x + 2)
        self.player_manager.stay(0.6 + random_number(0.1))
        self.poll_conn()
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['059285fa'].end_x - 2)
        self.player_manager.stay(0.7 + random_number(0.1))
        self.navigate_to_platform('444ae3dc')  # above the platform
        ### above the platform
        self.player_manager.stay(0.2 + random_number(0.1))
        self.player_manager.optimized_horizontal_move(self.terrain_analyzer.platforms['444ae3dc'].end_x - 20)
        self.player_manager.exorcist_charm()
        self.player_manager.stay(0.6 + random_number(0.1))
