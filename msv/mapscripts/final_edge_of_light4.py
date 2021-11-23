import time
from msv.macro_script import MacroController
from msv.util import random_number
import msv.directinput_constants as dc


# the final edge of light 4 script
class Fel4MacroController(MacroController):
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
        if (not self.elite_boss_detected and self.current_platform_hash == 'b73e5168'
                and time.time() - self.last_pickup_money_time > self.pickup_money_interval):
            self.pickup_money()
            self.last_pickup_money_time = time.time()
            return

        if self.current_platform_hash == 'b73e5168':  # left middle
            self.player_manager.shiki_exo_shiki(65)
        elif self.current_platform_hash == 'cb718da9' or self.current_platform_hash == '0ee7b532':
            self.player_manager.shikigami_haunting_sweep_move(65)
            if self.current_platform_hash == '0ee7b532':
                self.player_manager.teleport_up()
            else:
                self.player_manager.teleport_down()
        else:
            self.navigate_to_platform('b73e5168')  # left middle

        ### Other buffs
        self.buff_skills(yuki=False)

        # Finished
        return 0

    def pickup_money(self):
        self.logger.info('pick up money')
        if self.player_manager.is_skill_usable('true_arachnid_reflection'):
            self.player_manager.use_set_skill('true_arachnid_reflection')
        self.navigate_to_platform('0ee7b532')  # bottom

        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['0ee7b532'].start_x + 2)
        time.sleep(0.1)
        self.poll_conn()

        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['e4d256f5'].end_x - 12)  # middle right
        self.poll_conn()

        self.update()
        self.navigate_to_platform('e4d256f5')  # middle right
        self.keyhandler.single_press(dc.DIK_LEFT)
        self.player_manager.shikigami_haunting()
        self.player_manager.stay(0.35 + random_number(0.1))
        self.poll_conn()

        # Quick other player sound notify
        if self.screen_processor.find_other_player_marker():
            self.alert_sound(2)

        self.update()
        self.navigate_to_platform('2531794a')  # top right
        self.keyhandler.single_press(dc.DIK_LEFT)
        self.player_manager.shikigami_haunting()
        self.player_manager.stay(0.3 + random_number(0.1))
        self.poll_conn()

        self.update()
        self.navigate_to_platform('cb718da9')  # top left
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['cb718da9'].start_x + 5)
        self.player_manager.stay(0.45 + random_number(0.1))
