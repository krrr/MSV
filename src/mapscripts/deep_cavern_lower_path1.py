import time
from macro_script import MacroController
import directinput_constants as dc


# deep cavern lower path 1 script
class Dclp1MacroController(MacroController):
    def __init__(self, keymap, logger_queue):
        super().__init__(keymap=keymap, log_queue=logger_queue)
        self.last_pickup_money_time = time.time() + 30

    def loop(self):
        self._loop_common_job()

        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        if self.current_platform_hash in ('ab2972bd', '600f8ed9'):  # at center top or bottom
            if self.set_skills():
                return

        if self.current_platform_hash == '600f8ed9':  # center bottom
            if self.player_manager.x <= 83 + self.player_manager.horizontal_goal_offset:
                self.player_manager.shikigami_haunting_sweep_move(107)
                self.player_manager.shikigami_haunting_sweep_move(83, 20)
            else:
                self.player_manager.shikigami_haunting_sweep_move(83)

            self.keyhandler.single_press(dc.DIK_LEFT)
            self.player_manager.shikigami_haunting()
            self.player_manager.teleport_up()
        elif self.current_platform_hash == 'ab2972bd':  # center top
            # pickup money
            if time.time() - self.last_pickup_money_time > 80:
                self.pickup_money()
                self.last_pickup_money_time = time.time()
                return

            if self.player_manager.x <= 83 + self.player_manager.horizontal_goal_offset:
                self.keyhandler.single_press(dc.DIK_LEFT)
                self.player_manager.shikigami_haunting()
                self.keyhandler.single_press(dc.DIK_RIGHT)
                self.player_manager.shikigami_haunting()
            else:
                self.player_manager.shikigami_haunting_sweep_move(83)
                self.player_manager.shikigami_haunting()

            self.player_manager.teleport_down()
        else:
            self.navigate_to_platform('600f8ed9')  # center bottom

        ### Other buffs
        self.buff_skills()
        time.sleep(0.05)

        # Finished
        self.loop_count += 1
        return 0

    def pickup_money(self):
        # at center top now
        # right platforms first
        self.logger.info('pick up money')
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['ab2972bd'].end_x - 2)
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['ab2972bd'].end_x + 4)
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['85e71f57'].start_x + 2)  # right middle
        self.keyhandler.single_press(dc.DIK_RIGHT)
        self.player_manager.shikigami_haunting()
        time.sleep(0.22 + abs(self.player_manager.random_duration(0.1)))
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['0269c864'].end_x - 7)  # right right middle
        self.player_manager.shikigami_haunting()
        self.keyhandler.single_press(dc.DIK_LEFT)
        self.player_manager.shikigami_haunting()
        time.sleep(0.22 + abs(self.player_manager.random_duration(0.1)))
        self.player_manager.teleport_left()

        self.navigate_to_platform('600f8ed9')  # center bottom

        # then left platforms
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['ab2972bd'].start_x + 6)
        self.navigate_to_platform('ab2972bd')  # center top
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['ab2972bd'].start_x + 2)
        self.player_manager.shikigami_haunting()
        self.player_manager.teleport_left()
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['a08fae82'].start_x + 4)  # left top
        time.sleep(0.15 + abs(self.player_manager.random_duration(0.1)))
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['a08fae82'].end_x + 5)  # left top
        self.player_manager.shikigami_haunting()
        time.sleep(0.2 + abs(self.player_manager.random_duration(0.1)))
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['b0d5f01d'].start_x - 5)  # left middle
        time.sleep(0.2 + abs(self.player_manager.random_duration(0.1)))

        self.navigate_to_platform('600f8ed9')  # center bottom
