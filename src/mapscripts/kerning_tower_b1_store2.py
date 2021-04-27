import time
from macro_script import MacroController


class KerningTowerB1Store2(MacroController):
    def loop(self):
        # ignore rune

        # set skills
        if not self.elite_boss_detected and self.set_skills(combine=True):
            return

        if self.current_platform_hash == '385f30f0':  # center
            self.player_manager.shiki_exo_shiki(75, wait=False)
        elif self.current_platform_hash == '385f30f0':  # bottom
            self.player_manager.shikigami_haunting_sweep_move(75)
            self.player_manager.teleport_up()
        else:
            self.navigate_to_platform('385f30f0')  # center

        ### Other buffs
        self.buff_skills(yuki=False)
        time.sleep(0.05)

        # Finished
        self.loop_count += 1
        return 0
