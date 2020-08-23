import time
from macro_script import MacroController


# cavern upper path script
class CupMacroController(MacroController):
    def __init__(self, keymap, logger_queue):
        super().__init__(keymap=keymap, log_queue=logger_queue)
        self.last_pickup_money_time = time.time() + 80
        self.money_picked = False

    def loop(self):
        self._loop_common_job()

        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        if self.current_platform_hash in ('543f340d', '4b5aa172'):
            # will goto center bottom
            if self.set_skills():
                return

        if self.current_platform_hash == '543f340d':  # center bottom
            # pickup money and go back
            if time.time() - self.last_pickup_money_time > 80:
                self.pickup_money()
                self.last_pickup_money_time = time.time()
                return

            self.player_manager.optimized_horizontal_move(106)
            time.sleep(0.1)
            for _ in range(3):
                self.player_manager.jump()
                time.sleep(0.09 + abs(self.player_manager.random_duration(0.01)))
                self.player_manager.teleport_up()
                time.sleep(0.2)
                self.screen_processor.update_image(set_focus=False)
                player_pos = self.screen_processor.find_player_minimap_marker()
                if player_pos[1] < 30:
                    break
                time.sleep(1)
        elif self.current_platform_hash == '9769210f':  # left top
            self.player_manager.shikigami_haunting_sweep_move(51)
            if self.money_picked:
                self.player_manager.teleport_left()
                self.money_picked = False
            else:
                self.player_manager.jumpl()
                time.sleep(0.04)
                self.player_manager.shikigami_haunting()
                time.sleep(0.04)
                self.player_manager.shikigami_haunting()
        elif self.current_platform_hash == '4768c4f7':  # left left top
            self.player_manager.horizontal_move_goal(31)
            self.player_manager.teleport_down()
            time.sleep(0.4 + abs(self.player_manager.random_duration(0.1)))
        elif self.current_platform_hash == 'c99d319c':  # left left middle
            self.player_manager.shikigami_haunting()
            time.sleep(0.4 + abs(self.player_manager.random_duration(0.1)))
            self.player_manager.teleport_down()
            time.sleep(0.3 + abs(self.player_manager.random_duration(0.1)))
            self.player_manager.shikigami_haunting()
        elif self.current_platform_hash == '4b5aa172':  # left bottom
            self.player_manager.shikigami_haunting_sweep_move(79)
            self.player_manager.drop()
            time.sleep(0.7 + abs(self.player_manager.random_duration(0.1)))
            self.player_manager.shikigami_haunting()
        else:
            self.navigate_to_platform('543f340d')

        ### Other buffs
        self.player_manager.holy_symbol()
        self.player_manager.speed_infusion()
        self.player_manager.haku_reborn()
        time.sleep(0.05)

        # Finished
        self.loop_count += 1
        return 0

    def pickup_money(self):
        self.logger.info('pick up money')
        self.navigate_to_platform('f8358df9')  # right bottom

        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['f8358df9'].end_x - 9)
        time.sleep(0.1 + abs(self.player_manager.random_duration(0.1)))
        self.player_manager.horizontal_move_goal(self.terrain_analyzer.platforms['bb5c96fa'].end_x - 5)  # right top
        self.player_manager.teleport_up()
        self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.platforms['bb5c96fa'].start_x + 3)
        time.sleep(0.1 + abs(self.player_manager.random_duration(0.1)))
        self.player_manager.teleport_left()
        self.money_picked = True
