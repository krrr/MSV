import keystate_manager as km
import player_controller as pc
import screen_processor as sp
import terrain_analyzer as ta
import directinput_constants as dc
import rune_solver as rs
import logging, math, time, random


class CustomLogger:
    def __init__(self, logger_obj, logger_queue):
        self.logger_obj = logger_obj
        self.logger_queue = logger_queue

    def debug(self, *args):
        self.logger_obj.debug(" ".join([str(x) for x in args]))
        if self.logger_queue:
            self.logger_queue.put(("log", " ".join([str(x) for x in args])))

    def exception(self, *args):
        self.logger_obj.exception(" ".join([str(x) for x in args]))
        if self.logger_queue:
            self.logger_queue.put(("log", " ".join([str(x) for x in args])))


class MacroController:
    def __init__(self, keymap=km.DEFAULT_KEY_MAP, rune_model_dir=r"arrow_classifier_keras_gray.h5", log_queue=None):
        #sys.excepthook = self.exception_hook
        self.screen_capturer = sp.MapleScreenCapturer()
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(logging.DEBUG)
        self.log_queue = log_queue
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        fh = logging.FileHandler("logging.log")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        self.logger = CustomLogger(logger, self.log_queue)
        self.logger.debug("%s init" % self.__class__.__name__)
        self.screen_processor = sp.StaticImageProcessor(self.screen_capturer)
        self.terrain_analyzer = ta.PathAnalyzer()
        self.keyhandler = km.KeyboardInputManager()
        self.player_manager = pc.PlayerController(self.keyhandler, self.screen_processor, keymap)


        self.last_platform_hash = None
        self.current_platform_hash = None
        self.goal_platform_hash = None

        self.platform_error = 3  # If y value is same as a platform and within 3 pixels of platform border, consider to be on said platform

        self.rune_model_path = rune_model_dir
        self.rune_solver = rs.RuneDetector(self.rune_model_path, screen_capturer=self.screen_capturer, key_mgr=self.keyhandler)
        self.rune_platform_offset = 2

        self.loop_count = 0  # How many loops did we loop over?
        self.reset_navmap_loop_count = 10  # every x times reset navigation map, scrambling pathing
        self.navmap_reset_type = 1  # navigation map reset type. 1 for random, -1 for just reset. GETS ALTERNATED

        self.restrict_moonlight_slash_probability = 5

        self.platform_fail_loops = 0
        # How many loops passed and we are not on a platform?

        self.platform_fail_loop_threshold = 10
        # If self.platform_fail_loops is greater than threshold, run unstick()

        self.unstick_attempts = 0
        # If not on platform, how many times did we attempt unstick()?

        self.unstick_attempts_threshold = 5
        # If unstick after this amount fails to get us on a known platform, abort abort.

        self.logger.debug("%s init finished"%self.__class__.__name__)

    def load_and_process_platform_map(self, path):
        ret = self.terrain_analyzer.load(path)
        self.terrain_analyzer.generate_solution_dict()
        if ret != 0:
            self.logger.debug("Loaded platform data %s" % path)
        else:
            raise Exception("Failed to load platform data %s" % path)

    def distance(self, x1, y1, x2, y2):
        return math.sqrt((x1-x2)**2 + (y1-y2)**2)

    def find_current_platform(self):
        current_platform_hash = None

        for key, platform in self.terrain_analyzer.oneway_platforms.items():
            if self.player_manager.y >= min(platform.start_y, platform.end_y) and \
                    self.player_manager.y <= max(platform.start_y, platform.end_y) and \
                    self.player_manager.x >= platform.start_x and \
                    self.player_manager.x <= platform.end_x:
                current_platform_hash = platform.hash
                break

        for key, platform in self.terrain_analyzer.platforms.items():
            if self.player_manager.y == platform.start_y and \
                    self.player_manager.x >= platform.start_x and \
                    self.player_manager.x <= platform.end_x:
                current_platform_hash = platform.hash
                break

        #  Add additional check to take into account imperfect platform coordinates
        for key, platform in self.terrain_analyzer.platforms.items():
            if self.player_manager.y == platform.start_y and \
                    self.player_manager.x >= platform.start_x - self.platform_error and \
                    self.player_manager.x <= platform.end_x + self.platform_error:
                current_platform_hash = platform.hash
                break

        if current_platform_hash:
            return current_platform_hash
        else:
            return 0

    def find_coord_platform(self, coord):
        """
        Checks if a rune exists on a platform and if exists, returns platform hash
        :return: Platform hash if located, else None
        """
        self.player_manager.update()
        if coord:
            platform_hash = None
            for key, platform in self.terrain_analyzer.platforms.items():
                if coord[1] >= platform.start_y - self.rune_platform_offset and \
                        coord[1] <= platform.start_y + self.rune_platform_offset and \
                        coord[0] >= platform.start_x and \
                        coord[0] <= platform.end_x:
                    platform_hash = key
            for key, platform in self.terrain_analyzer.oneway_platforms.items():
                if coord[1] >= platform.start_y - self.rune_platform_offset and \
                        coord[1] <= platform.start_y + self.rune_platform_offset and \
                        coord[0] >= platform.start_x and \
                        coord[0] <= platform.end_x:
                    platform_hash = key

            if platform_hash:
                return platform_hash

        return None

    def navigate_to_platform(self, platform_hash, coord):
        """
        Automatically goes to rune_coords by calling find_rune_platform. Update platform information before calling.
        :return: 0
        """
        if self.current_platform_hash != platform_hash:
            solutions = self.terrain_analyzer.pathfind(self.current_platform_hash, platform_hash)
            if solutions:
                self.logger.debug("paths to platform %s: %s" % (platform_hash, " ".join(x.method for x in solutions)))
                for solution in solutions:
                    if self.player_manager.x < solution.lower_bound[0]:
                        # We are left of solution bounds.
                        self.player_manager.optimized_horizontal_move(solution.lower_bound[0])
                    else:
                        # We are right of solution bounds
                        self.player_manager.optimized_horizontal_move(solution.upper_bound[0])
                    movement_type = solution.method
                    if movement_type == ta.METHOD_DROP:
                        self.player_manager.drop()
                        time.sleep(1)
                    elif movement_type == ta.METHOD_JUMPL:
                        self.player_manager.jumpl()
                        time.sleep(0.5)
                    elif movement_type == ta.METHOD_JUMPR:
                        self.player_manager.jumpr()
                        time.sleep(0.5)
                    elif movement_type == ta.METHOD_TELEPORTL:
                        self.player_manager.teleport_left()
                        time.sleep(0.3)
                    elif movement_type == ta.METHOD_TELEPORTR:
                        self.player_manager.teleport_right()
                        time.sleep(0.3)
                    elif movement_type == ta.METHOD_TELEPORTUP:
                        self.player_manager.teleport_up()
                        time.sleep(0.3)
                time.sleep(0.3)
            else:
                self.logger.debug("could not generate path to rune platform %s from starting platform %s" % (platform_hash, self.current_platform_hash))
        return 0

    def log_skill_usage_statistics(self):
        """
        checks self.player_manager.skill_cast_time and count and logs them if time is greater than threshold
        :return: None
        """
        if not self.player_manager.skill_counter_time:
            self.player_manager.skill_counter_time = time.time()
        if time.time() - self.player_manager.skill_counter_time > 60:

            self.logger.debug("skills casted in duration %d: %d skill/s: %f"%(int(time.time() - self.player_manager.skill_counter_time), self.player_manager.skill_cast_counter, self.player_manager.skill_cast_counter/int(time.time() - self.player_manager.skill_counter_time)))
            self.player_manager.skill_cast_counter = 0
            self.player_manager.skill_counter_time = time.time()

    def loop(self):
        """
        Main event loop for Macro
        Important note: Since this function uses PathAnalyzer's pathing algorithm, when this function moves to a new
        platform, it will invoke PathAnalyzer.move_platform. HOWEVER, in an attempt to make the system error-proof,
        platform movement and solution flagging is done on the loop call succeeding the loop call where the actual
        movement is made. self.goal_platform is used for such purpose.
        :return: loop exit code
        exit code information:
            0: all good
            -1: problem in image processing
            -2: problem in navigation/pathing
        """
        # Check if MapleStory window is alive
        random.seed((time.time() * 10**4) % 10 **3)

        self.log_skill_usage_statistics()

        if not self.screen_capturer.ms_get_screen_hwnd():
            self.logger.debug("Failed to get MS screen rect")
            self.abort()
            return -1

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

        # Update navigation dictionary with last_platform and current_platform
        if self.goal_platform_hash and self.current_platform_hash == self.goal_platform_hash:
            self.terrain_analyzer.move_platform(self.last_platform_hash, self.current_platform_hash)

        # Reinitialize last_platform to current_platform
        self.last_platform_hash = self.current_platform_hash

        if self.loop_count % self.reset_navmap_loop_count == 0 and self.loop_count != 0:
            # Reset navigation map to randomize pathing
            self.terrain_analyzer.generate_solution_dict()
            numbers = []
            for x in range(0, len(self.terrain_analyzer.platforms.keys())):
                numbers.append(x)
            random.shuffle(numbers)
            idx = 0
            if self.navmap_reset_type == 1:
                for key, platform in self.terrain_analyzer.platforms.items():
                    platform.last_visit = numbers[idx]
                    idx += 1

            self.navmap_reset_type *= -1
            self.logger.debug("navigation map reset and randomized at loop #%d"%(self.loop_count))

        # Rune Detector
        self.player_manager.update()
        rune_coords = self.screen_processor.find_rune_marker()
        rune_platform_hash = self.find_coord_platform(rune_coords) if rune_coords else None
        if rune_platform_hash:
            self.logger.debug("need to solve rune at platform {0}".format(rune_platform_hash))
            rune_solve_time_offset = (time.time() - self.player_manager.last_rune_solve_time)
            if rune_solve_time_offset >= self.player_manager.rune_cooldown or rune_solve_time_offset <= 30:
                self.navigate_to_platform(rune_platform_hash, rune_coords)
                time.sleep(0.3)
                self.player_manager.shikigami_haunting_sweep_move(rune_coords[0])
                self.player_manager.horizontal_move_goal(rune_coords[0])
                time.sleep(0.1)
                self.keyhandler.single_press(dc.DIK_PERIOD)
                time.sleep(1.5)
                solve_result = self.rune_solver.solve_auto()
                self.logger.debug("rune_solver.solve_auto results: %d" % (solve_result))
                if solve_result == -1:
                    self.logger.debug("rune_solver.solve_auto failed to solve")
                    for x in range(4):
                        self.keyhandler.single_press(dc.DIK_LEFT)

                self.player_manager.last_rune_solve_time = time.time()
                self.current_platform_hash = rune_platform_hash
                time.sleep(0.5)
        # End Rune Detector

        # We are on a platform. find an optimal way to clear platform.
        # If we know our next platform destination, we can make our path even more efficient
        next_platform_solution = self.terrain_analyzer.select_move(self.current_platform_hash)
        self.logger.debug("next destination: %s method: %s" % (next_platform_solution.to_hash, next_platform_solution.method))
        self.goal_platform_hash = next_platform_solution.to_hash

        # lookahead pathing
        lookahead_platform_solution = self.terrain_analyzer.select_move(self.goal_platform_hash)
        lookahead_solution_lb = lookahead_platform_solution.lower_bound
        lookahead_solution_ub = lookahead_platform_solution.upper_bound

        #lookahead_lb = lookahead_lb[0] if lookahead_lb[0] >= next_platform_solution.lower_bound[0] else next_platform_solution.lower_bound[0]
        #lookahead_ub = lookahead_ub[0] if lookahead_ub[0] <= next_platform_solution.upper_bound[0] else next_platform_solution.upper_bound[0]

        if lookahead_solution_lb[0] < next_platform_solution.lower_bound[0] and lookahead_solution_ub[0] > next_platform_solution.lower_bound[0] or \
                lookahead_solution_lb[0] > next_platform_solution.lower_bound[0] and lookahead_solution_lb[0] < next_platform_solution.upper_bound[0]:
            lookahead_lb = lookahead_solution_lb[0] if lookahead_solution_lb[0] >= next_platform_solution.lower_bound[0] and lookahead_solution_lb[0] <= next_platform_solution.upper_bound[0] else next_platform_solution.lower_bound[0]
            lookahead_ub = lookahead_solution_ub[0] if lookahead_solution_ub[0] <= next_platform_solution.upper_bound[0] and lookahead_solution_ub[0] >= next_platform_solution.lower_bound[0] else next_platform_solution.upper_bound[0]
        else:
            lookahead_lb = next_platform_solution.lower_bound[0]
            lookahead_ub = next_platform_solution.upper_bound[0]

        lookahead_lb += random.randint(0, 2)
        lookahead_ub -= random.randint(0, 2)

        # end lookahead pathing

        # Start skill usage section
        if (abs(self.player_manager.x - next_platform_solution.lower_bound[0]) <
                abs(self.player_manager.x - next_platform_solution.upper_bound[0])):
            self.keyhandler.single_press(dc.DIK_RIGHT)
        else:
            self.keyhandler.single_press(dc.DIK_LEFT)
        self.player_manager.shikigami_haunting()
        # End skill usage

        # Find coordinates to move to next platform
        if self.player_manager.x >= next_platform_solution.lower_bound[0] and self.player_manager.x <= next_platform_solution.upper_bound[0]:
            # We are within the solution bounds. attack within solution range and move
            if abs(self.player_manager.x - next_platform_solution.lower_bound[0]) < abs(self.player_manager.x - next_platform_solution.upper_bound[0]):
                # We are closer to lower boound, so move to upper bound to maximize movement
                in_solution_movement_goal = lookahead_ub
            else:
                in_solution_movement_goal = lookahead_lb

            self.player_manager.shikigami_haunting_sweep_move(in_solution_movement_goal, no_attack_distance=self.player_manager.shikigami_haunting_range)
        else:
            # We need to move within the solution bounds. First, find closest solution bound which can cover majority of current platform.
            if self.player_manager.x < next_platform_solution.lower_bound[0]:
                # We are left of solution bounds.
                self.player_manager.shikigami_haunting_sweep_move(lookahead_ub, no_attack_distance=self.player_manager.shikigami_haunting_range)
            else:
                # We are right of solution bounds
                self.player_manager.shikigami_haunting_sweep_move(lookahead_lb, no_attack_distance=self.player_manager.shikigami_haunting_range)

        time.sleep(0.1)

        # All movement and attacks finished. Now perform movement
        movement_type = next_platform_solution.method
        if movement_type == ta.METHOD_DROP:
            self.player_manager.drop()
            time.sleep(1)
        elif movement_type == ta.METHOD_JUMPL:
            self.player_manager.jumpl()
            time.sleep(0.7)
        elif movement_type == ta.METHOD_JUMPR:
            self.player_manager.jumpr()
            time.sleep(0.7)
        elif movement_type == ta.METHOD_TELEPORTL:
            self.player_manager.teleport_left()
            time.sleep(0.5)
        elif movement_type == ta.METHOD_TELEPORTR:
            self.player_manager.teleport_right()
            time.sleep(0.5)
        elif movement_type == ta.METHOD_TELEPORTUP:
            self.player_manager.teleport_up()
            time.sleep(0.5)

        #End inter-platform movement

        # Other buffs
        self.player_manager.holy_symbol()
        self.player_manager.speed_infusion()
        self.player_manager.haku_reborn()
        time.sleep(0.05)

        # set skills
        if (self.terrain_analyzer.kishin_shoukan_coord and
                time.time() - self.player_manager.last_kishin_shoukan_time > self.player_manager.kishin_shoukan_cooldown):
            platform = self.find_coord_platform(self.terrain_analyzer.kishin_shoukan_coord)
            if platform:
                self.logger.debug('placing kishin shoukan')
                self.navigate_to_platform(platform, self.terrain_analyzer.kishin_shoukan_coord)
                self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.kishin_shoukan_coord[0])
                self.player_manager.horizontal_move_goal(self.terrain_analyzer.kishin_shoukan_coord[0])
                self.player_manager.kishin_shoukan()
                self.player_manager.last_kishin_shoukan_time = time.time()

        if (self.terrain_analyzer.yaksha_boss_coord and
                time.time() - self.player_manager.last_yaksha_boss_time > self.player_manager.yaksha_boss_cooldown):
            platform = self.find_coord_platform(self.terrain_analyzer.yaksha_boss_coord)
            if platform:
                self.logger.debug('placing yaksha boss')
                self.navigate_to_platform(platform, self.terrain_analyzer.yaksha_boss_coord)
                self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.yaksha_boss_coord[0])
                self.player_manager.horizontal_move_goal(self.terrain_analyzer.yaksha_boss_coord[0])
                self.keyhandler.single_press(dc.DIK_RIGHT)
                self.player_manager.yaksha_boss()
                self.player_manager.last_yaksha_boss_time = time.time()

        # Finished
        self.loop_count += 1
        return 0

    def unstick(self):
        """
        Run when script can't find which platform we are at.
        Solution: try random stuff to attempt it to reposition it self
        :return: None
        """
        # try to get off ladder
        self.player_manager.jumpr()
        time.sleep(1.2)
        if self.find_current_platform():
            return 0

        self.player_manager.teleport_up()
        time.sleep(0.7)
        if self.find_current_platform():
            return 0

        self.player_manager.teleport_right()
        time.sleep(0.7)
        if self.find_current_platform():
            return 0

        self.player_manager.teleport_left()
        time.sleep(0.7)
        if self.find_current_platform():
            return 0

    def abort(self):
        self.keyhandler.reset()
        self.logger.debug("aborted")
        if self.log_queue:
            self.log_queue.put(["stopped", None])
