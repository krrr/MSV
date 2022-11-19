import time, random
from msv.terrain_analyzer import MoveMethod
from msv import macro_script


class MacroControllerAStar(macro_script.MacroController):
    """
    This is a new port of MacroController from macro_script with improved pathing. MacroController Used PlatforScan,
    which is an tree search algorithm I implemented, and works at indivisual platform level. However, V2 uses A* path
    finding and works at pixel level, which allows more randomized and fluent moving.
    """
    def loop(self):
        """
        Main event loop for Macro
        Will now use current coordinates and A* to find a new path.
        :return: loop exit code(same as macro_script.py)
        """
        random.seed((time.time() * 10**4) % 10 **3)

        if not self.player_manager.skill_counter_time:
            self.player_manager.skill_counter_time = time.time()
        if time.time() - self.player_manager.skill_counter_time > 60:
            print("skills casted in duration %d: %d skill/s: %f"%(int(time.time() - self.player_manager.skill_counter_time), self.player_manager.skill_cast_counter, self.player_manager.skill_cast_counter/int(time.time() - self.player_manager.skill_counter_time)))
            self.logger.debug("skills casted in duration %d: %d skill/s: %f skill/s"%(int(time.time() - self.player_manager.skill_counter_time), self.player_manager.skill_cast_counter, self.player_manager.skill_cast_counter/int(time.time() - self.player_manager.skill_counter_time)))
            self.player_manager.skill_cast_counter = 0
            self.player_manager.skill_counter_time = time.time()
        if not self.screen_capturer.get_game_hwnd():
            self.abort("failed to get MS screen rect")

        # Update Screen
        self.screen_processor.update_image(set_focus=False)
        # Update Constants
        player_minimap_pos = self.screen_processor.find_player_minimap_marker()
        if not player_minimap_pos:
            return -1
        self.player_manager.update(player_minimap_pos[0], player_minimap_pos[1])

        # Placeholder for Lie Detector Detector (sounds weird)

        # End Placeholder

        # Check if player is on platform
        self.current_platform_hash = None
        get_current_platform = self.find_current_platform()
        if not get_current_platform:
            # Move to nearest platform and redo loop
            # Failed to find platform.
            self.platform_fail_loops += 1
            if self.platform_fail_loops >= self.platform_fail_loop_threshold:
                self.logger.debug("stuck. attempting unstick()...")
                self.unstick_attempts += 1
                self.unstick()
            if self.unstick_attempts >= self.unstick_attempts_threshold:
                self.logger.debug("unstick() threshold reached. sending error code..")
                return -2
            else:
                return 0
        else:
            self.platform_fail_loops = 0
            self.unstick_attempts = 0
            self.current_platform_hash = get_current_platform

        self.player_manager.update()

        # Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return
        # End Rune Detector

        # Start inter-platform movement
        dest_platform_hash = random.choice([key for key in self.terrain_analyzer.platforms.keys() if key != self.current_platform_hash])
        dest_platform = self.terrain_analyzer.platforms[dest_platform_hash]
        self.player_manager.update()
        random_platform_coord = (random.randint(dest_platform.start_x, dest_platform.end_x), dest_platform.start_y)
        # Once we have selected the platform to move, we can generate a path using A*
        pathlist = self.terrain_analyzer.astar_pathfind((self.player_manager.x, self.player_manager.y), random_platform_coord)
        print(pathlist)
        for mid_coord, method in pathlist:
            self.player_manager.update()
            print(mid_coord, method)
            if method == MoveMethod.MOVER or method == MoveMethod.MOVEL:
                self.player_manager.optimized_horizontal_move(mid_coord[0])
            elif method == MoveMethod.ROPE_UP:
                # interdelay = self.terrain_analyzer.calculate_vertical_doublejump_delay(self.player_manager.y, mid_coord[1])
                # print(interdelay)
                self.player_manager.rope_up()
            elif method == MoveMethod.DROP:
                self.player_manager.drop()
        # End inter-platform movement

        # Other buffs
        self.buff_skills()
        time.sleep(0.05)

        # set skills
        # self.player_manager.star_vortex()

        # Finished
        self.loop_count += 1
        return 0

    def navigate_to_platform(self, platform_hash):
        """
        Uses A* pathfinding to navigate to rune coord
        :return: None
        """
        pass