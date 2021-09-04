import time
from msv.macro_script import MacroController
from msv.util import random_number
import msv.directinput_constants as dc


# deep cavern lower path 1 script
class Dclp1MacroController(MacroController):
    def __init__(self, keymap, log_queue, cmd_queue, config):
        super().__init__(keymap, log_queue, cmd_queue, config)
        self.last_pickup_money_time = time.time() + 20

    def loop(self):
        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        # set skills
        if self.current_platform_hash in ('ab2972bd', '600f8ed9'):  # at center top or bottom
            if not self.elite_boss_detected and self.set_skills():
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
            if not self.elite_boss_detected and time.time() - self.last_pickup_money_time > self.pickup_money_interval:
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

        # Finished
        return 0

    def pickup_money(self, return1=False):
        # assume at center top now
        # right platforms first
        self.logger.info('pick up money')

        no_attack = self.other_player_detected_start and (self.player_manager.is_skill_key_set('yuki_musume')
                                                          or self.player_manager.is_skill_key_set('mihile_link'))
        if no_attack and self.player_manager.is_skill_key_set('yuki_musume'):
            self.player_manager.yuki_musume()

        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['ab2972bd'].end_x - 2)
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['ab2972bd'].end_x + 4)
        self.check_cmd_queue()
        time.sleep(0.1)
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['85e71f57'].start_x + 2)  # right middle

        if no_attack:
            self.keyhandler.single_press(dc.DIK_RIGHT)
            self.check_cmd_queue()
            time.sleep(0.95 + random_number(0.1))
            self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['0269c864'].end_x - 3)  # right right middle
            self.keyhandler.single_press(dc.DIK_LEFT)
            time.sleep(0.6)
        else:
            self.keyhandler.single_press(dc.DIK_RIGHT)
            self.player_manager.shikigami_haunting()
            self.check_cmd_queue()
            time.sleep(0.6 + random_number(0.1))
            self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['0269c864'].end_x - 6)  # right right middle
            self.player_manager.shikigami_haunting()
            self.keyhandler.single_press(dc.DIK_LEFT)
            self.player_manager.shikigami_haunting()
            time.sleep(0.25)

        self.check_cmd_queue()
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['600f8ed9'].end_x - 3)  # center bottom
        time.sleep(0.55)

        self.check_cmd_queue()
        self.update()
        # Quick other player sound notify
        if self.screen_processor.find_other_player_marker():
            self.alert_sound(2)

        self.navigate_to_platform('600f8ed9')  # ensure at center bottom

        if time.time() - self.player_manager.last_skill_use_time['yaksha_boss'] <= 10:
            self.player_manager.last_skill_use_time['yaksha_boss'] = 0  # force setting yaksha boss
        self._place_set_skill('yaksha_boss')

        # then left platforms
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['ab2972bd'].start_x + 6)
        self.update()
        self.navigate_to_platform('ab2972bd')  # center top
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['ab2972bd'].start_x + 2)
        self.player_manager.shikigami_haunting()
        self.player_manager.teleport_left()
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['a08fae82'].start_x + 3)  # left top
        self.keyhandler.single_press(dc.DIK_RIGHT)
        self.player_manager.shikigami_haunting()
        time.sleep(0.15 + random_number(0.1))
        self.player_manager.teleport_right()

        if return1:  # alternative preset will stay at left middle platform
            time.sleep(0.05)
            return

        self.keyhandler.single_press(dc.DIK_LEFT)
        self.player_manager.shikigami_haunting()
        time.sleep(0.2 + random_number(0.1))
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['b0d5f01d'].start_x - 5)  # left middle
        time.sleep(0.2 + random_number(0.1))

        self.update()
        self.navigate_to_platform('600f8ed9')  # center bottom
