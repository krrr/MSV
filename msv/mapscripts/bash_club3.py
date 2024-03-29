from msv.macro_script import MacroController


class BashClub3(MacroController):
    def loop(self):
        # ignore rune

        # set skills
        if self.set_skills(combine=True):
            return

        if self.current_platform_hash == '07dad985':  # center right
            self.player_manager.shiki_exo_shiki(142, wait=False)
        elif self.current_platform_hash == 'a4ed61ba':  # bottom
            self.player_manager.shikigami_haunting_sweep_move(142)
            self.player_manager.teleport_up()
        else:
            self.navigate_to_platform('07dad985')  # center right

        ### Other buffs
        self.buff_skills(yuki=False)

        # Finished
        return 0
