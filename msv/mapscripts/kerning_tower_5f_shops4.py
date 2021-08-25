from msv.macro_script import MacroController


class KerningTower5FShops4(MacroController):
    def loop(self):
        # ignore rune

        # set skills
        if not self.elite_boss_detected and self.set_skills(combine=True):
            return

        if self.current_platform_hash == 'de353c1f':  # center left
            self.player_manager.shiki_exo_shiki(67, wait=False)
        elif self.current_platform_hash == 'dc710317':  # bottom
            self.player_manager.shikigami_haunting_sweep_move(70)
            self.player_manager.teleport_up()
        else:
            self.navigate_to_platform('de353c1f')  # center left

        ### Other buffs
        self.buff_skills(yuki=False)

        # Finished
        return 0
