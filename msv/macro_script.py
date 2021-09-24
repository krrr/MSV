import os
import datetime
import logging, math, time, random
import msv.directinput_constants as dc
import msv.player_controller as pc
import msv.input_manager as km
from multiprocessing.connection import Connection
from msv.terrain_analyzer import PathAnalyzer, MoveMethod
from msv import driver
from msv.screen_processor import ScreenProcessor, StaticImageProcessor, MiniMapError, GameCaptureError
from msv.player_controller import PlayerController
from msv.rune_solver.rune_solver_simple import RuneSolverSimple
from msv.util import get_config, get_file_log_handler, ConnLoggerHandler, random_number


def macro_process_main(conn: Connection):
    from msv import mapscripts
    # noinspection PyUnresolvedReferences
    import msv.resources_rc  # for reading qt resource in child process

    logger = logging.getLogger("macro_loop")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_file_log_handler())

    macro = None

    while True:
        command = conn.recv()
        try:
            if command[0] == "start":
                logger.debug("starting MacroController...")
                keymap, platform_file_dir, preset = command[1:]
                config = get_config()
                if preset:
                    macro = mapscripts.map_scripts[preset](keymap, conn, config)
                else:
                    macro = MacroController(keymap, conn, config)
                macro.load_and_process_platform_map(platform_file_dir)

                macro.loop_entry()
            elif command[0] == 'stop':
                if macro:
                    macro.abort(raise_=False)
                    macro = None
        except CommandReceived:  # break from inner loop
            pass
        except Aborted:
            macro = None
        except Exception:  # unknown error
            logger.exception("Exception during loop execution:")
            conn.send(("exception", None))
            break

    conn.close()


class CommandReceived(Exception):
    pass


class Aborted(Exception):
    pass


class MacroController:
    FIND_PLATFORM_OFFSET = 2
    ERROR_RETRY_LIMIT = 5
    RUNE_FAIL_CD = 5

    def __init__(self, keymap=km.DEFAULT_KEY_MAP, conn=None, config=None):
        if config is None:
            config = {}
        self.conn = conn
        self.debug = config.get('debug', False)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        if not self.logger.hasHandlers():
            self.logger.addHandler(ConnLoggerHandler(logging.DEBUG, conn))
            self.logger.addHandler(get_file_log_handler())
        self.logger.debug("%s init" % self.__class__.__name__)

        kernel_driver = config.get('kernel_driver', False)
        if kernel_driver:
            # need to get driver handle on this new process
            try:
                driver.get_driver_handle()
            except Exception as e:
                self.logger.error('failed to get kernel driver handle: ' + str(e))
                kernel_driver = False

        self.auto_resolve_rune = config.get('auto_solve_rune', True)
        self.screen_capturer = ScreenProcessor()
        self.screen_processor = StaticImageProcessor(self.screen_capturer)
        self.terrain_analyzer = PathAnalyzer()
        self.keyhandler = km.InputManager(use_driver=kernel_driver)
        self.player_manager = pc.PlayerController(self.keyhandler, self.screen_processor, keymap)

        self.last_platform_hash = None
        self.current_platform_hash = None
        self.goal_platform_hash = None

        self.platform_error = 3  # if x within 3 pixels of platform border, consider to be on said platform

        self.last_rune_solve_time = 0
        self.rune_fail_count = 0
        # self.rune_model_path = config.get('rune_model_dir', 'arrow_classifier_keras_gray.h5')
        # self.rune_solver = rs.RuneDetectorSimple(self.rune_model_path, screen_capturer=self.screen_capturer, key_mgr=self.keyhandler)
        self.rune_solver = RuneSolverSimple(screen_capturer=self.screen_capturer, key_mgr=self.keyhandler)

        self.loop_count = 0  # How many loops did we loop over?
        self.reset_navmap_loop_count = 10  # every x times reset navigation map, scrambling pathing
        self.navmap_reset_type = 1  # navigation map reset type. 1 for random, -1 for just reset. GETS ALTERNATED

        self.restrict_moonlight_slash_probability = 5

        self.platform_fail_loops = 0  # How many loops passed and we are not on a platform?
        self.platform_fail_loop_threshold = 10  # If self.platform_fail_loops is greater than threshold, run unstick()
        self.unstick_attempts = 0  # If not on platform, how many times did we attempt unstick()?
        self.unstick_attempts_threshold = 5  # abort if unstick after this amount fails to get us on a known platform

        self.pickup_money_interval = 90
        self.other_player_detected_start = None
        self.player_pos_not_found_start = None
        self.elite_boss_detected = False

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

        for p in self.terrain_analyzer.platforms.values():
            if self.player_manager.is_on_platform(p):
                current_platform_hash = p.hash
                break

        if current_platform_hash is None:
            #  Add additional check to take into account imperfect platform coordinates
            for p in self.terrain_analyzer.platforms.values():
                if self.player_manager.is_on_platform(p, self.platform_error):
                    current_platform_hash = p.hash
                    break

        return current_platform_hash

    def find_coord_platform(self, coord):
        """
        Locate platform by coordinate
        """
        if not coord:
            return None
        for key, platform in self.terrain_analyzer.platforms.items():
            if (platform.start_y - self.FIND_PLATFORM_OFFSET <= coord[1] <= platform.start_y + self.FIND_PLATFORM_OFFSET and
                    platform.start_x <= coord[0] <= platform.end_x):
                return key

        return None

    def navigate_to_platform(self, platform_hash):
        """
        Move to platform by various methods
        """
        for i in range(3):  # retry up to 3 times
            if self.current_platform_hash == platform_hash:
                return True
            elif self.current_platform_hash is None:
                return False

            solutions = self.terrain_analyzer.pathfind(self.current_platform_hash, platform_hash)
            if not solutions:
                self.logger.error("generate path failed: platform %s -> %s" % (self.current_platform_hash, platform_hash))
                return False

            self.logger.debug("path to platform %s: %s" % (platform_hash, ", ".join(str(x.method) for x in solutions)))
            for solution in solutions:
                curr_platform = self.terrain_analyzer.platforms[self.current_platform_hash]
                next_platform = self.terrain_analyzer.platforms[solution.to_hash]

                if solution.method == MoveMethod.TELEPORTR:
                    x = max(self.player_manager.x, next_platform.start_x + random.randint(4, 5) - PlayerController.TELEPORT_HORIZONTAL_RANGE)
                elif solution.method == MoveMethod.TELEPORTL:
                    x = min(self.player_manager.x, next_platform.end_x - random.randint(4, 5) + PlayerController.TELEPORT_HORIZONTAL_RANGE)
                elif solution.method == MoveMethod.JUMPR or solution.method == MoveMethod.MOVER:
                    x = curr_platform.end_x - random.randint(2, 3)
                elif solution.method == MoveMethod.JUMPL or solution.method == MoveMethod.MOVEL:
                    x = curr_platform.start_x + random.randint(2, 3)
                else:  # overlap platform (teleport up/down or drop)
                    if solution.lower_bound[0] < self.player_manager.x < solution.upper_bound[0]:
                        x = self.player_manager.x
                    else:
                        closer_to_next_lower = (abs(self.player_manager.x - solution.lower_bound[0]) <
                                                abs(self.player_manager.x - solution.upper_bound[0]))
                        x = solution.lower_bound[0] + 2 if closer_to_next_lower else solution.upper_bound[0] - 2

                self.player_manager.shikigami_haunting_sweep_move(x)
                self.player_manager.horizontal_move_goal(x)

                self._player_move(solution)

                self.poll_conn()
                self.update()
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
        """Must be done job.
        :return: loop exit code
        exit code information:
            0: all good
            -1: problem in image processing
            -2: problem in navigation/pathing
            -3: white room detected
            -4: GM detected
        """
        self.poll_conn()

        random.seed((time.time() * 10**4) % 10 ** 3)

        self.log_skill_usage_statistics()

        # Check if MapleStory window is alive
        if not self.screen_capturer.get_game_hwnd():
            self.abort('failed to get MS screen rect')

        # Update Screen
        self.screen_processor.update_image(set_focus=False)

        # Update Constants
        player_pos = self.screen_processor.find_player_minimap_marker()
        if not player_pos:
            white_room = self.screen_processor.check_white_room()
            if self.player_pos_not_found_start is None:
                self.player_pos_not_found_start = time.time()
                if white_room:
                    self.conn.send(('play', 'white_room'))
                    self.logger.info('white room detected')
                    self.save_current_screen('white_room')

            if white_room:
                return -3
            else:
                raise MiniMapError('player pos not found')
        else:
            self.player_pos_not_found_start = None
        self.player_manager.update(player_pos[0], player_pos[1])

        ### GM check
        if self.screen_processor.check_gm_cap():
            self.conn.send(('play', 'white_room'))
            self.logger.info('GM detected')
            self.save_current_screen('gm')
            return -4

        ### Other player check
        other_pos = self.screen_processor.find_other_player_marker()
        if other_pos:  # Other player present
            if self.other_player_detected_start is None:
                self.logger.info('other player detected')
                self.other_player_detected_start = time.time()
            self.alert_sound(2)
        else:
            self.other_player_detected_start = None

        ### Elite boss check
        if self.screen_processor.check_elite_boss():
            if not self.elite_boss_detected:
                self.logger.info('elite boss detected')
            self.elite_boss_detected = True
            if other_pos:
                if time.time() - self.other_player_detected_start >= 5:
                    self.save_current_screen('eboss_people')
                    self.exit_to_ch_select()
                    self.abort('eboss present and other player staying')
            else:
                self.alert_sound(1)
        else:
            if self.elite_boss_detected:
                self.logger.info('elite boss gone')
            self.elite_boss_detected = False

        ### Dialog box check
        if self.screen_processor.check_dialog():
            self.keyhandler.single_press(dc.DIK_ESCAPE)

        self.current_platform_hash = self.find_current_platform()
        ### Check if player is on platform
        if not self.current_platform_hash:
            # Move to nearest platform and redo loop
            # Failed to find platform.
            self.platform_fail_loops += 1
            if self.platform_fail_loops >= self.platform_fail_loop_threshold:
                self.logger.warning("stuck. attempting unstick()...")
                self.unstick()
            if self.unstick_attempts >= self.unstick_attempts_threshold:
                self.abort('unstick threshold reached')
            return -2
        else:
            self.platform_fail_loops = 0
            self.unstick_attempts = 0

        return 0

    def update(self):
        self.player_manager.update()  # will update image
        self.current_platform_hash = self.find_current_platform()

    def loop_entry(self):
        retry_err_count = 0
        while True:
            try:
                ret = self._loop_common_job()
                if ret != 0:
                    continue

                retry_err_count = 0
                self.loop()
                self.loop_count += 1
            except (GameCaptureError, MiniMapError) as e:
                if retry_err_count > self.ERROR_RETRY_LIMIT:
                    self.abort(str(e))
                else:
                    if retry_err_count == 0:
                        self.logger.warning(str(e) + ', retry...')
                    time.sleep(1 if retry_err_count < 2 else 2)
                    retry_err_count += 1

    def loop(self):
        """
        Main event loop for Macro
        Important note: Since this function uses PathAnalyzer's pathing algorithm, when this function moves to a new
        platform, it will invoke PathAnalyzer.move_platform. HOWEVER, in an attempt to make the system error-proof,
        platform movement and solution flagging is done on the loop call succeeding the loop call where the actual
        movement is made. self.goal_platform is used for such purpose.
        """
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

            self.player_manager.shikigami_haunting_sweep_move(in_solution_movement_goal, no_attack_distance=PlayerController.SHIKIGAMI_HAUNTING_RANGE)
        elif sweep:
            # We need to move within the solution bounds. First, find closest solution bound which can cover majority of current platform.
            if self.player_manager.x < next_platform_solution.lower_bound[0]:
                # We are left of solution bounds.
                self.player_manager.shikigami_haunting_sweep_move(lookahead_ub, no_attack_distance=PlayerController.SHIKIGAMI_HAUNTING_RANGE)
            else:
                # We are right of solution bounds
                self.player_manager.shikigami_haunting_sweep_move(lookahead_lb, no_attack_distance=PlayerController.SHIKIGAMI_HAUNTING_RANGE)

        # time.sleep(0.1)

        ### Other buffs
        self.buff_skills()
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

    def buff_skills(self, yuki=True):
        skills = ['holy_symbol', 'speed_infusion', 'haku_reborn', 'mihile_link']
        if yuki:
            skills.append('yuki_musume')
        random.shuffle(skills)
        used = False
        for i in skills:
            # add extra delay to first buff skill; following skill should not add delay if already used any skill
            temp = getattr(self.player_manager, i)(wait_before=0 if used else 0.35)
            used = used or temp

        return used

    def _rune_detect_solve(self):
        rune_coords = self.screen_processor.find_rune_marker()
        if rune_coords:
            # warning if auto solve disabled or failed too many times
            if not self.auto_resolve_rune or self.rune_fail_count >= 3:
                self.alert_sound(1)
            if not self.auto_resolve_rune or time.time() - self.last_rune_solve_time < self.RUNE_FAIL_CD:
                return
        else:
            self.rune_fail_count = 0
            return

        # go to rune platform
        rune_platform_hash = self.find_coord_platform(rune_coords)
        if not rune_platform_hash:
            self.logger.error('failed to find rune platform')
            return
        msg = "solve rune at platform " + rune_platform_hash
        if self.rune_fail_count > 0:
            msg += ' (%s fails)' % self.rune_fail_count
        self.logger.info(msg)
        if not self.navigate_to_platform(rune_platform_hash):
            self.logger.warning('failed to navigate to rune platform')
            return

        self.player_manager.shikigami_haunting_sweep_move(rune_coords[0])
        self.player_manager.horizontal_move_goal(rune_coords[0])
        self.player_manager.wait_teleport_cd()
        time.sleep(0.2)
        self.keyhandler.single_press(self.player_manager.keymap["interact"])
        time.sleep(1.5)
        if self.debug:  # save image to disk for future use
            self.save_current_screen('rune')
        solve_result = self.rune_solver.solve_auto()
        if solve_result is None:
            self.rune_fail_count += 1
            self.logger.error("failed to solve rune")
            self.keyhandler.single_press(self.player_manager.keymap["interact"])
        else:
            self.logger.debug("rune_solver.solve_auto results: %s" % (solve_result))

        self.last_rune_solve_time = time.time()
        self.current_platform_hash = rune_platform_hash
        time.sleep(0.05 + random_number(0.05))

    def _player_move(self, solution):
        move_method = solution.method
        if move_method == MoveMethod.DROP:
            self.player_manager.drop()
        elif move_method == MoveMethod.JUMPL:
            self.player_manager.jump_left()
        elif move_method == MoveMethod.JUMPR:
            self.player_manager.jump_right()
        elif move_method in (MoveMethod.TELEPORTL, MoveMethod.TELEPORTR, MoveMethod.TELEPORTUP, MoveMethod.TELEPORTDOWN):
            self.player_manager.wait_teleport_cd()

            if move_method == MoveMethod.TELEPORTL:
                self.player_manager.teleport_left()
            elif move_method == MoveMethod.TELEPORTR:
                self.player_manager.teleport_right()
            elif move_method == MoveMethod.TELEPORTUP:
                self.player_manager.teleport_up()
            elif move_method == MoveMethod.TELEPORTDOWN:
                self.player_manager.teleport_down()

            time.sleep(0.1)

    def set_skills(self, combine=False):
        if self.elite_boss_detected and self.other_player_detected_start is not None:
            return False

        self.update()
        if self.current_platform_hash is None:
            return False

        if combine:
            is_set = self._place_set_skill('yaksha_boss')
            self.poll_conn()
            self.update()
            if self.current_platform_hash is None:
                return is_set
            if is_set:
                self._place_set_skill('nightmare_invite')
                self.poll_conn()
                self._place_set_skill('kishin_shoukan')
                self.update()
                return True
            else:
                return False
        else:
            is_set = False
            for i in ('kishin_shoukan', 'yaksha_boss', 'nightmare_invite'):
                is_set = any((is_set, self._place_set_skill(i)))
                self.update()
                if self.current_platform_hash is None:
                    return is_set
                self.poll_conn()
            return is_set

    def _place_set_skill(self, skill_name):
        """Placing set skill at specific location"""
        if not self.player_manager.is_skill_usable(skill_name):
            return False

        coord = self.terrain_analyzer.set_skill_coord.get(skill_name)
        if not coord:
            return False
        platform = self.find_coord_platform(coord)
        if not platform:
            self.logger.warning('placing skill ' + skill_name + 'coord not found: ' + str(coord))
            return False
        self.logger.info('placing ' + skill_name.replace('_', ' '))
        if not self.navigate_to_platform(platform):
            return False
        self.player_manager.shikigami_haunting_sweep_move(coord[0])
        self.player_manager.horizontal_move_goal(coord[0])
        if skill_name == 'yaksha_boss':
            dir_ = dc.DIK_LEFT if self.terrain_analyzer.other_attrs.get('yaksha_boss_dir') == 'left' else dc.DIK_RIGHT
            self.keyhandler.single_press(dir_)
        time.sleep(0.1)
        self.player_manager.use_set_skill(skill_name)
        self.player_manager.last_skill_use_time[skill_name] = time.time()

        return True

    def unstick(self):
        """
        Run when script can't find which platform we are at.
        Solution: try random stuff to attempt it to reposition it self
        :return:
        """
        self.unstick_attempts += 1
        # jump right to try to get off ladder
        for method in (self.player_manager.jump_right, self.player_manager.teleport_up,
                       self.player_manager.teleport_left, self.player_manager.teleport_right):
            method()
            time.sleep(0.8)
            self.update()
            if self.current_platform_hash is not None:
                return True
        return False

    def poll_conn(self):
        if self.conn and self.conn.poll():
            self.keyhandler.reset()
            raise CommandReceived()

    def abort(self, reason='', raise_=True):
        self.keyhandler.reset()
        self.logger.info('macro stopped' + (': ' + reason if reason else ''))
        if self.conn:
            self.conn.send(('stopped', None))
        if raise_:
            raise Aborted

    def alert_sound(self, times):
        self.conn.send(('alert_sound', times))

    def exit_to_ch_select(self):
        for k in (dc.DIK_ESCAPE, dc.DIK_UP, dc.DIK_RETURN, dc.DIK_RETURN):
            self.keyhandler.single_press(k)
            time.sleep(0.2 + random_number(0.04, minus=True))

    def save_current_screen(self, prefix):
        img = self.screen_capturer.capture_pil()

        if not os.path.isdir('screenshots'):
            os.mkdir('screenshots')
        time_str = datetime.datetime.now().replace(microsecond=0).isoformat().replace(':', '_')
        with open('screenshots/' + prefix + '_' + time_str + '.png', 'wb') as f:
            img.save(f)

