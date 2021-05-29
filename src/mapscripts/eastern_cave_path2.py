import time
from macro_script import MacroController
import directinput_constants as dc


class EasternCavePath2(MacroController):
    LEFT_X = 62
    RIGHT_X = 174
    LEFT_PORTAL_X = 43
    RIGHT_PORTAL_X = 196

    def loop(self):
        # ignore rune

        # set skills
        if (self.current_platform_hash in ('0ed3f4ca', '30fcb02b')   # at bottom
                and not self.elite_boss_detected and self.set_skills(combine=True)):
            return

        if self.current_platform_hash == '0ed3f4ca':  # left platform
            self.action(True)
        elif self.current_platform_hash == 'a9b881ce':  # right platform
            self.action(False)
        else:
            self.navigate_to_platform('0ed3f4ca' if self.player_manager.x < 120 else 'a9b881ce')

        ### Other buffs
        self.buff_skills(yuki=False)
        time.sleep(0.05)

        # Finished
        self.loop_count += 1
        return 0

    def action(self, is_left):
        x = self.LEFT_X if is_left else self.RIGHT_X
        portal_x = self.LEFT_PORTAL_X if is_left else self.RIGHT_PORTAL_X
        if abs(self.player_manager.x - portal_x) <= self.player_manager.horizontal_goal_offset:
            self.keyhandler.single_press(dc.DIK_RIGHT if is_left else dc.DIK_LEFT)
            self.player_manager.shikigami_haunting(wait_delay=False)
            self.player_manager.teleport_right() if is_left else self.player_manager.teleport_left()
            time.sleep(0.05)
            self.player_manager.horizontal_move_goal(x)
            time.sleep(0.2)
            self.player_manager.shikigami_haunting()
        else:
            self.player_manager.shikigami_haunting_sweep_move(x)
            self.player_manager.wait_teleport_cd()
        self.player_manager.exorcist_charm(wait_delay=False)
        time.sleep(1 + abs(self.player_manager.random_duration(0.05)))
        self.player_manager.teleport_left() if is_left else self.player_manager.teleport_right()
        time.sleep(0.05)
        self.update()
        self.use_portal('0ed3f4ca' if is_left else 'a9b881ce', portal_x)

    def use_portal(self, platform, x):
        self.player_manager.horizontal_move_goal(x, precise=True)
        while True:
            self.keyhandler.single_press(dc.DIK_UP)
            time.sleep(0.05)
            self.keyhandler.single_press(dc.DIK_UP)
            time.sleep(0.05)
            self.update()
            if self.current_platform_hash != platform or abs(self.player_manager.x - x) > 6:
                break
            self.player_manager.horizontal_move_goal(x, precise=True)

            self.check_cmd_queue()
