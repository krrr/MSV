from msv.macro_script import MacroController


class KerningTower2FCafe4(MacroController):
    def loop(self):
        # ignore rune

        # set skills
        if self.set_skills(combine=True):
            return

        if self.current_platform_hash == '5187c647':  # center left 1
            self.player_manager.shiki_exo_shiki(38, wait=False)
            self.navigate_to_platform('cf9d0814')
        elif self.current_platform_hash == 'cf9d0814':  # center left 2
            self.player_manager.shiki_exo_shiki(62, wait=False)
            self.navigate_to_platform('5187c647')
        elif self.current_platform_hash == 'f6820bad':  # bottom
            self.player_manager.shikigami_haunting_sweep_move(62 if self.player_manager.x > 50 else 38)
            self.player_manager.teleport_up()
        else:
            self.navigate_to_platform('cf9d0814')  # center left 2

        ### Other buffs
        self.buff_skills(yuki=False)

        # Finished
        return 0
