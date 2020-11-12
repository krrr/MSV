import time
from .deep_cavern_lower_path1 import Dclp1MacroController
import directinput_constants as dc


# deep cavern lower path 1 alternative script
class Dclp1MacroControllerAlt(Dclp1MacroController):
    def __init__(self, keymap, logger_queue):
        super().__init__(keymap=keymap, logger_queue=logger_queue)
        self.last_pickup_money_time = time.time() + 20

    def loop(self):
        self._loop_common_job()

        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        if self.set_skills(combine=True):
            return

        # pickup money
        if time.time() - self.last_pickup_money_time > self.pickup_money_interval:
            self.navigate_to_platform('ab2972bd')  # center top
            self.pickup_money(True)
            self.last_pickup_money_time = time.time()
            return

        if self.current_platform_hash == 'b0d5f01d':  # left middle
            if not (72 <= self.player_manager.x <= 75):
                self.player_manager.horizontal_move_goal(73)

            dir = dc.DIK_RIGHT if self.player_manager.x < 73.5 else dc.DIK_LEFT
            self.keyhandler.single_press(dir)
            self.player_manager.shikigami_haunting()
            time.sleep(0.05)
            self.player_manager.exorcist_charm(False)
            time.sleep(1.23 + abs(self.player_manager.random_duration(0.04)))
            self.keyhandler.single_press(dc.DIK_LEFT if dir == dc.DIK_RIGHT else dc.DIK_LEFT)
            self.player_manager.shikigami_haunting()
            time.sleep(1.23 + abs(self.player_manager.random_duration(0.04)))
        elif self.current_platform_hash == '600f8ed9':  # center bottom
            self.player_manager.shikigami_haunting_sweep_move(70)
            self.player_manager.teleport_up()
        elif self.current_platform_hash == 'ab2972bd':  # center top
            left_edge = self.terrain_analyzer.platforms['ab2972bd'].start_x
            self.player_manager.shikigami_haunting_sweep_move(left_edge + 5)
            self.player_manager.horizontal_move_goal(left_edge - 4)
        else:
            self.navigate_to_platform('b0d5f01d')  # left middle

        ### Other buffs
        self.buff_skills()
        time.sleep(0.05)

        # Finished
        self.loop_count += 1
        return 0
