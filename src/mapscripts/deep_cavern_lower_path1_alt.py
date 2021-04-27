import time
from .deep_cavern_lower_path1 import Dclp1MacroController


# deep cavern lower path 1 alternative script
class Dclp1MacroControllerAlt(Dclp1MacroController):
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
            self.navigate_to_platform('ab2972bd')  # center top
            self.pickup_money(True)
            self.last_pickup_money_time = time.time()
            return

        if self.current_platform_hash == 'b0d5f01d':  # left middle
            self.player_manager.shiki_exo_shiki(73)
        elif self.current_platform_hash == '600f8ed9':  # center bottom
            self.player_manager.shikigami_haunting_sweep_move(70)
            self.player_manager.teleport_up()
        elif self.current_platform_hash == 'ab2972bd':  # center top
            left_edge = self.terrain_analyzer.platforms['ab2972bd'].start_x
            self.player_manager.shikigami_haunting_sweep_move(left_edge + 5)
            self.player_manager.horizontal_move_goal(left_edge - 4)
            time.sleep(0.095)
        else:
            self.navigate_to_platform('b0d5f01d')  # left middle

        ### Other buffs
        self.buff_skills(yuki=False)
        time.sleep(0.05)

        # Finished
        self.loop_count += 1
        return 0
