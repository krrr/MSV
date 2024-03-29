import time
from msv.macro_script import MacroController
from msv.util import random_number
import msv.directinput_constants as dc


# cavern upper path script
class CupMacroController(MacroController):
    def __init__(self, conn, config):
        super().__init__(conn, config)
        self.last_pickup_money_time = time.time() + 20
        self.money_picked = False

    def loop(self):
        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        if self.current_platform_hash in ('543f340d', '4b5aa172'):  # at center bottom or left bottom
            # will goto center bottom
            if self.set_skills():
                return

        if self.current_platform_hash == '543f340d':  # center bottom
            # pickup money and go back
            if time.time() - self.last_pickup_money_time > self.pickup_money_interval:
                self.pickup_money()
                self.last_pickup_money_time = time.time()
                return

            if self.player_manager.x >= 108:
                self.player_manager.optimized_horizontal_move(108)
            self.player_manager.drop()
            time.sleep(random_number(0.08))
            self.keyhandler.single_press(dc.DIK_RIGHT)
            self.player_manager.shikigami_haunting()
        elif self.current_platform_hash == '9769210f':  # left top
            if self.player_manager.x <= 51 + self.player_manager.horizontal_goal_offset:
                self.keyhandler.single_press(dc.DIK_LEFT)
            else:
                self.player_manager.shikigami_haunting_sweep_move(51)

            if self.money_picked:
                self.player_manager.teleport_left()
                self.money_picked = False
            else:
                self.player_manager.jump_left(wait=False)
                time.sleep(0.04)
                self.player_manager.shikigami_haunting()
                time.sleep(0.058)
                self.player_manager.shikigami_haunting()
        elif self.current_platform_hash == '4768c4f7':  # left left top
            self.player_manager.horizontal_move_goal(31)
            self.player_manager.teleport_down()
            time.sleep(0.1 + random_number(0.1))
        elif self.current_platform_hash == 'c99d319c':  # left left middle
            self.keyhandler.single_press(dc.DIK_LEFT)
            self.player_manager.shikigami_haunting()
            self.player_manager.horizontal_move_goal(21)
            time.sleep(0.4 + random_number(0.1))
            self.player_manager.teleport_down()
            time.sleep(0.2 + random_number(0.1))
            self.player_manager.shikigami_haunting()
        elif self.current_platform_hash == '4b5aa172':  # left bottom
            self.player_manager.shikigami_haunting_sweep_move(60)
            self.player_manager.drop(wait=False)
            self.player_manager.shikigami_haunting()
            time.sleep(0.3 + random_number(0.08))
            self.player_manager.shikigami_haunting()
        else:
            self.navigate_to_platform('543f340d')

        ### Other buffs
        self.buff_skills()

        # Finished
        return 0

    def pickup_money(self):
        self.logger.info('pick up money')
        self.navigate_to_platform('f8358df9')  # right bottom

        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['f8358df9'].end_x - 9)
        time.sleep(0.2 + random_number(0.1))
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['bb5c96fa'].end_x - 5)  # right top
        self.player_manager.teleport_up()
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['bb5c96fa'].start_x + 3)
        time.sleep(0.2 + random_number(0.1))
        self.player_manager.teleport_left()
        self.money_picked = True
