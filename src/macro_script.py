import os
import datetime
import logging, math, time, random
import win32api, win32con
import keystate_manager as km
import player_controller as pc
import screen_processor as sp
import terrain_analyzer
from terrain_analyzer import MoveMethod
import directinput_constants as dc
from rune_solver.rune_solver_simple import RuneSolverSimple
from util import get_config


class CustomLoggerHandler(logging.Handler):
    def __init__(self, level, logger_queue):
        super().__init__(level)
        self.logger_queue = logger_queue

    def emit(self, record):
        if self.logger_queue:
            self.logger_queue.put(("log", self.format(record)))


class MacroController:
    def __init__(self, keymap=km.DEFAULT_KEY_MAP, rune_model_dir=r"arrow_classifier_keras_gray.h5", log_queue=None):
        self.log_queue = log_queue
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.hasHandlers():
            self.logger.addHandler(CustomLoggerHandler(logging.DEBUG, log_queue))
            fh = logging.FileHandler("logging.log")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(fh)
        self.logger.info("%s init" % self.__class__.__name__)

        self.auto_resolve_rune = get_config().get('auto_solve_rune', True)
        self.screen_capturer = sp.MapleScreenCapturer()
        self.screen_processor = sp.StaticImageProcessor(self.screen_capturer)
        self.terrain_analyzer = terrain_analyzer.PathAnalyzer()
        self.keyhandler = km.KeyboardInputManager()
        self.player_manager = pc.PlayerController(self.keyhandler, self.screen_processor, keymap)

        self.last_platform_hash = None
        self.current_platform_hash = None
        self.goal_platform_hash = None

        self.platform_error = 3  # If y value is same as a platform and within 3 pixels of platform border, consider to be on said platform

        self.rune_model_path = rune_model_dir
        # self.rune_solver = rs.RuneDetectorSimple(self.rune_model_path, screen_capturer=self.screen_capturer, key_mgr=self.keyhandler)
        self.rune_solver = RuneSolverSimple(screen_capturer=self.screen_capturer, key_mgr=self.keyhandler)
        self.find_platform_offset = 2

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

        self.logger.debug("%s init finished" % self.__class__.__name__)

    def load_and_process_platform_map(self, path):
        ret = self.terrain_analyzer.load(path)
        self.terrain_analyzer.generate_solution_dict()
        if ret != 0:
            self.logger.info("Loaded platform data %s" % path)
        else:
            raise Exception("Failed to load platform data %s" % path)

    def distance(self, x1, y1, x2, y2):
        return math.sqrt((x1-x2)**2 + (y1-y2)**2)

    def find_current_platform(self):
        current_platform_hash = None

        for key, platform in self.terrain_analyzer.platforms.items():
            if self.player_manager.is_on_platform(platform):
                current_platform_hash = platform.hash
                break

        if current_platform_hash is None:
            #  Add additional check to take into account imperfect platform coordinates
            for key, platform in self.terrain_analyzer.platforms.items():
                if self.player_manager.is_on_platform(platform, self.platform_error):
                    current_platform_hash = platform.hash
                    break

        return current_platform_hash

    def find_coord_platform(self, coord):
        """
        Locate platform by coordinate
        """
        self.player_manager.update()
        if not coord:
            return None
        for key, platform in self.terrain_analyzer.platforms.items():
            if (platform.start_y - self.find_platform_offset <= coord[1] <= platform.start_y + self.find_platform_offset and
                    platform.start_x <= coord[0] <= platform.end_x):
                return key

        return None

    def navigate_to_platform(self, platform_hash):
        """
        """

        for i in range(3):
            if self.current_platform_hash == platform_hash:
                return True
            elif self.current_platform_hash is None:
                return False

            solutions = self.terrain_analyzer.pathfind(self.current_platform_hash, platform_hash)
            if not solutions:
                self.logger.error("could not generate path to platform %s from platform %s" % (platform_hash, self.current_platform_hash))
                return False

            self.logger.debug("path to platform %s: %s" % (platform_hash, ", ".join(str(x.method) for x in solutions)))
            for solution in solutions:
                curr_platform = self.terrain_analyzer.platforms[self.current_platform_hash]

                if solution.method == MoveMethod.TELEPORTR or solution.method == MoveMethod.JUMPR:
                    x = curr_platform.end_x - random.randint(2, 3)
                elif solution.method == MoveMethod.TELEPORTL or solution.method == MoveMethod.JUMPL:
                    x = curr_platform.start_x + random.randint(2, 3)
                else:  # overlap platform
                    closer_to_next_lower = (abs(self.player_manager.x - solution.lower_bound[0]) <
                                            abs(self.player_manager.x - solution.upper_bound[0]))
                    x = solution.lower_bound[0] + 2 if closer_to_next_lower else solution.upper_bound[0] - 2

                self.player_manager.shikigami_haunting_sweep_move(x)
                self.player_manager.horizontal_move_goal(x)

                self._player_move(solution)

                self.player_manager.update()
                self.current_platform_hash = self.find_current_platform()

                if self.current_platform_hash != solution.to_hash:  # should retry
                    if self.current_platform_hash is None:  # in case stuck in ladder
                        self.logger.warning("stuck. attempting unstick()...")
                        self.unstick()
                    break

            if i != 0:
                time.sleep(0.5)  # wait before try again

        return False

    def log_skill_usage_statistics(self):
        """
        checks self.player_manager.skill_cast_time and count and logs them if time is greater than threshold
        :return: None
        """
        if not self.player_manager.skill_counter_time:
            self.player_manager.skill_counter_time = time.time()
        if time.time() - self.player_manager.skill_counter_time > 60:
            self.logger.info("skills casted in duration %d: %d skill/s: %f"%(int(time.time() - self.player_manager.skill_counter_time), self.player_manager.skill_cast_counter, self.player_manager.skill_cast_counter/int(time.time() - self.player_manager.skill_counter_time)))
            self.player_manager.skill_cast_counter = 0
            self.player_manager.skill_counter_time = time.time()

    def _loop_common_job(self):
        """Must be done job"""
        # Check if MapleStory window is alive
        random.seed((time.time() * 10**4) % 10 **3)

        self.log_skill_usage_statistics()

        if not self.screen_capturer.ms_get_screen_hwnd():
            self.logger.error("Failed to get MS screen rect")
            self.abort()
            return -1

        # Update Screen
        self.screen_processor.update_image(set_focus=False)

        # Update Constants
        player_pos = self.screen_processor.find_player_minimap_marker()
        if not player_pos:
            return -1
        self.player_manager.update(player_pos[0], player_pos[1])

        # Other player sound notify
        if self.screen_processor.find_other_player_marker():
            self.alert_sound()

        ### Placeholder for Lie Detector Detector (sounds weird)
        ### End Placeholder

        # Check if player is on platform
        self.current_platform_hash = self.find_current_platform()
        if not self.current_platform_hash:
            # Move to nearest platform and redo loop
            # Failed to find platform.
            self.platform_fail_loops += 1
            if self.platform_fail_loops >= self.platform_fail_loop_threshold:
                self.logger.warning("stuck. attempting unstick()...")
                self.unstick()
            if self.unstick_attempts >= self.unstick_attempts_threshold:
                self.logger.warning("unstick() threshold reached. sending error code..")
                return -2
            else:
                return 0
        else:
            self.platform_fail_loops = 0
            self.unstick_attempts = 0

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
        ret = self._loop_common_job()
        if ret != 0:
            return ret

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
            self.logger.info("navigation map reset and randomized at loop #%d" % self.loop_count)

        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return
        ### End Rune Detector

        # We are on a platform. find an optimal way to clear platform.
        # If we know our next platform destination, we can make our path even more efficient
        next_platform_solution = self.terrain_analyzer.select_move(self.current_platform_hash)
        self.logger.info("next destination: %s method: %s" % (next_platform_solution.to_hash, next_platform_solution.method))
        self.goal_platform_hash = next_platform_solution.to_hash

        ### lookahead pathing
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

        lookahead_lb += random.randint(2, 3)
        lookahead_ub -= random.randint(2, 3)

        ### end lookahead pathing

        ### Start skill usage section
        closer_to_next_lower = (abs(self.player_manager.x - next_platform_solution.lower_bound[0]) <
                                abs(self.player_manager.x - next_platform_solution.upper_bound[0]))
        sweep = True
        no_sweep_dist_x = next_platform_solution.lower_bound[0] + 3 if closer_to_next_lower else next_platform_solution.upper_bound[0] - 3
        if (next_platform_solution.lower_bound[0] <= no_sweep_dist_x <= next_platform_solution.upper_bound[0] and
            (next_platform_solution.upper_bound[0] - next_platform_solution.lower_bound[0]) <= 44):
            self.player_manager.shikigami_haunting_sweep_move(no_sweep_dist_x)
            self.player_manager.horizontal_move_goal(no_sweep_dist_x)
            sweep = False
            time.sleep(0.05)

        if closer_to_next_lower:
            self.keyhandler.single_press(dc.DIK_RIGHT)
        else:
            self.keyhandler.single_press(dc.DIK_LEFT)
        self.player_manager.shikigami_haunting()
        ### End skill usage

        # Find coordinates to move to next platform
        if sweep and next_platform_solution.lower_bound[0] <= self.player_manager.x <= next_platform_solution.upper_bound[0]:
            # We are within the solution bounds. attack within solution range and move
            if closer_to_next_lower:
                # We are closer to lower bound, so move to upper bound to maximize movement
                in_solution_movement_goal = lookahead_ub
            else:
                in_solution_movement_goal = lookahead_lb

            self.player_manager.shikigami_haunting_sweep_move(in_solution_movement_goal, no_attack_distance=self.player_manager.shikigami_haunting_range)
        elif sweep:
            # We need to move within the solution bounds. First, find closest solution bound which can cover majority of current platform.
            if self.player_manager.x < next_platform_solution.lower_bound[0]:
                # We are left of solution bounds.
                self.player_manager.shikigami_haunting_sweep_move(lookahead_ub, no_attack_distance=self.player_manager.shikigami_haunting_range)
            else:
                # We are right of solution bounds
                self.player_manager.shikigami_haunting_sweep_move(lookahead_lb, no_attack_distance=self.player_manager.shikigami_haunting_range)

        # time.sleep(0.1)

        ### Other buffs
        self.player_manager.holy_symbol()
        self.player_manager.speed_infusion()
        self.player_manager.haku_reborn()
        time.sleep(0.05)
        ### End other buffs

        # All movement and attacks finished. Now perform movement
        self._player_move(next_platform_solution)
        # End inter-platform movement

        ### Start set skills
        self.set_skills()
        # End set skills

        # Finished
        self.loop_count += 1
        return 0

    def _rune_detect_solve(self):
        rune_coords = self.screen_processor.find_rune_marker()
        if not self.auto_resolve_rune:
            if rune_coords:
                self.alert_sound(1)
            return

        rune_platform_hash = self.find_coord_platform(rune_coords) if rune_coords else None
        if not rune_platform_hash:
            return

        self.logger.info("need to solve rune at platform {0}".format(rune_platform_hash))
        rune_solve_time_offset = (time.time() - self.player_manager.last_rune_solve_time)
        if rune_solve_time_offset >= self.player_manager.rune_fail_cooldown:
            if self.navigate_to_platform(rune_platform_hash):
                self.player_manager.shikigami_haunting_sweep_move(rune_coords[0])
                self.player_manager.horizontal_move_goal(rune_coords[0])
                time.sleep(0.1)
                self.keyhandler.single_press(dc.DIK_PERIOD)
                time.sleep(1.5)
                self.save_current_screen('rune')  # save image to disk for future use
                solve_result = self.rune_solver.solve_auto()
                if solve_result is None:
                    self.logger.error("rune_solver.solve_auto failed to solve")
                    self.keyhandler.single_press(self.player_manager.keymap["interact"])
                else:
                    self.logger.debug("rune_solver.solve_auto results: %s" % (solve_result))

                self.player_manager.last_rune_solve_time = time.time()
                self.current_platform_hash = rune_platform_hash
                time.sleep(0.5)
            else:
                self.logger.warning('failed to navigate to rune platform')

    def _player_move(self, solution):
        move_method = solution.method
        if move_method == MoveMethod.DROP:
            self.player_manager.drop()
            time.sleep(1)
        elif move_method == MoveMethod.TELEPORTDOWN:
            self.player_manager.teleport_down()
            time.sleep(0.5)
        elif move_method == MoveMethod.JUMPL:
            self.player_manager.jumpl()
            time.sleep(0.7)
        elif move_method == MoveMethod.JUMPR:
            self.player_manager.jumpr()
            time.sleep(0.7)
        elif move_method == MoveMethod.TELEPORTL:
            self.player_manager.teleport_left()
            time.sleep(0.5)
        elif move_method == MoveMethod.TELEPORTR:
            self.player_manager.teleport_right()
            time.sleep(0.5)
        elif move_method == MoveMethod.TELEPORTUP:
            self.player_manager.teleport_up()
            time.sleep(0.5)

    def set_skills(self):
        is_set = False
        self.player_manager.update()
        self.current_platform_hash = self.find_current_platform()
        if self.current_platform_hash is None:
            return is_set

        if (self.terrain_analyzer.kishin_shoukan_coord and
                time.time() - self.player_manager.last_kishin_shoukan_time > self.player_manager.kishin_shoukan_cooldown):
            platform = self.find_coord_platform(self.terrain_analyzer.kishin_shoukan_coord)
            if platform:
                self.logger.info('placing kishin shoukan')
                self.screen_processor.update_image(set_focus=False)
                if not self.navigate_to_platform(platform):
                    return is_set
                self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.kishin_shoukan_coord[0])
                self.player_manager.horizontal_move_goal(self.terrain_analyzer.kishin_shoukan_coord[0])
                time.sleep(0.1)
                self.player_manager.kishin_shoukan()
                self.player_manager.last_kishin_shoukan_time = time.time()

                self.player_manager.update()
                self.current_platform_hash = self.find_current_platform()
                is_set = True
                if self.current_platform_hash is None:
                    return is_set

        if (self.terrain_analyzer.yaksha_boss_coord and
                time.time() - self.player_manager.last_yaksha_boss_time > self.player_manager.yaksha_boss_cooldown):
            platform = self.find_coord_platform(self.terrain_analyzer.yaksha_boss_coord)
            if platform:
                self.logger.info('placing yaksha boss')
                self.screen_processor.update_image(set_focus=False)
                if not self.navigate_to_platform(platform):
                    return is_set

                self.player_manager.shikigami_haunting_sweep_move(self.terrain_analyzer.yaksha_boss_coord[0])
                self.player_manager.horizontal_move_goal(self.terrain_analyzer.yaksha_boss_coord[0])
                self.keyhandler.single_press(dc.DIK_RIGHT)
                time.sleep(0.1)
                self.player_manager.yaksha_boss()
                self.player_manager.last_yaksha_boss_time = time.time()
                is_set = True

        self.loop_count += 1
        return is_set

    def unstick(self):
        """
        Run when script can't find which platform we are at.
        Solution: try random stuff to attempt it to reposition it self
        :return:
        """
        self.unstick_attempts += 1
        # jump right to try to get off ladder
        for i in ['jumpr', 'teleport_up', 'teleport_left', 'teleport_right']:
            getattr(self.player_manager, i)()
            time.sleep(0.8)
            self.player_manager.update()
            if self.find_current_platform():
                return True
        return False

    def abort(self):
        self.keyhandler.reset()
        self.logger.info("aborted")
        if self.log_queue:
            self.log_queue.put(["stopped", None])

    def alert_sound(self, times=3):
        for _ in range(times):
            win32api.MessageBeep(win32con.MB_ICONWARNING)
            time.sleep(0.5)

    def save_current_screen(self, prefix):
        img = self.screen_capturer.capture()

        if not os.path.isdir('screenshots'):
            os.mkdir('screenshots')
        time_str = datetime.datetime.now().replace(microsecond=0).isoformat().replace(':', '_')
        with open('screenshots/' + prefix + '_' + time_str + '.png', 'wb') as f:
            img.save(f)

