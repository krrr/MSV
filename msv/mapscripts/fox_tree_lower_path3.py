from msv.macro_script import MacroController


class FoxTreeLowerPath3(MacroController):
    def loop(self):
        # ignore rune

        # set skills
        if not self.elite_boss_detected and self.set_skills(combine=True):
            return

        if self.current_platform_hash == '773b4dee':  # center
            self.player_manager.shiki_exo_shiki(37, wait=False)
        elif self.current_platform_hash == 'b5822ca6':  # bottom
            self.player_manager.shikigami_haunting_sweep_move(37)
            self.player_manager.teleport_up()
        elif self.current_platform_hash == '8f1abfca':  # yaksha platform
            self.player_manager.teleport_down()
        else:
            self.navigate_to_platform('773b4dee')  # center

        ### Other buffs
        self.buff_skills(yuki=False)

        # Finished
        return 0
