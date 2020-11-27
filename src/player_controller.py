from directinput_constants import DIK_RIGHT, DIK_DOWN, DIK_LEFT, DIK_UP
from keystate_manager import DEFAULT_KEY_MAP
import time, math, random


# simple jump vertical distance: about 6 pixels
class PlayerController:
    """
    This class keeps track of character location and manages advanced movement and attacks.
    """
    def __init__(self, key_mgr, screen_handler, keymap=DEFAULT_KEY_MAP):
        """
        Class Variables:

        self.x: Known player minimap x coord. Needs to be updated manually
        self.x: Known player minimap y coord. Needs tobe updated manually
        self.key_mgr: handle to KeyboardInputManager
        self.screen_processor: handle to StaticImageProcessor
        self.goal_x: If moving, destination x coord
        self.goal_y: If moving, destination y coord
        self.busy: True if current class is calling blocking calls or in a loop
        :param key_mgr: Handle to KeyboardInputManager
        :param screen_handler: Handle to StaticImageProcessor. Only used to call find_player_minimap_marker

        Bot States:
        Idle
        ChangePlatform
        AttackinPlatform
        """
        self.x = self.y = None

        self.keymap = {}
        for key, value in keymap.items():
            self.keymap[key] = value[0]
        self.key_mgr = key_mgr
        self.screen_processor = screen_handler
        self.goal_x = self.goal_y = None

        self.busy = False

        self.horizontal_goal_offset = 2

        self.x_movement_enforce_rate = 15  # refer to optimized_horizontal_move

        self.shikigami_haunting_range = 18
        self.shikigami_haunting_delay = 0.37  # delay after using shikigami haunting where character is not movable

        self.horizontal_movement_threshold = 18  # teleport instead of walk if distance greater than threshold

        self.skill_cast_counter = 0
        self.skill_counter_time = 0

        self.skill_cooldown = {
            'yaksha_boss': 30, 'kishin_shoukan': 60, 'nightmare_invite': 60
        }
        self.set_skill_common_delay = 1.4

        self.rune_fail_cooldown = 5
        self.last_rune_solve_time = 0

        self.v_buff_cd = 180  # common cool down for v buff
        self.buff_common_delay = 2  # common delay for v buff

        self.last_skill_use_time = {
            'yaksha_boss': 0, 'kishin_shoukan': 0, 'nightmare_invite': 0,
            'haku_reborn': 0, 'speed_infusion': 0, 'holy_symbol': 0, 'yuki_musume': 0, 'mihaha_link': 0
        }

    def update(self, player_coords_x=None, player_coords_y=None):
        """
        Updates self.x, self.y to input coordinates
        :param player_coords_x: Coordinates to update self.x
        :param player_coords_y: Coordinates to update self.y
        :return: None
        """
        if not player_coords_x:
            self.screen_processor.update_image()
            scrp_ret_val = self.screen_processor.find_player_minimap_marker()
            if scrp_ret_val:
                player_coords_x, player_coords_y = scrp_ret_val
            else:
                #raise Exception("screen_processor did not return coordinates!!")
                player_coords_x = self.x
                player_coords_y = self.y
        self.x, self.y = player_coords_x, player_coords_y

    def distance(self, coord1, coord2):
        return math.sqrt((coord1[0]-coord2[0])**2 + (coord1[1]-coord2[1])**2)

    def shikigami_haunting_sweep_move(self, goal_x, no_attack_distance=0):
        """
        This function will, while moving towards goal_x, constantly use shikigami haunting and not overlapping
        X coordinate max error on flat surface: +- 5 pixels
        :param goal_x: minimap x goal coordinate.
        :param no_attack_distance: Distance in x pixels where any attack skill would not be used and just move
        """
        self.update()
        start_x = self.x
        loc_delta = self.x - goal_x
        if abs(loc_delta) < self.horizontal_goal_offset:
            return True

        if not no_attack_distance:
            self.key_mgr.single_press(DIK_LEFT if loc_delta > 0 else DIK_RIGHT, 0.05)  # turn to correct direction

        start_time = time.time()
        time_limit = math.ceil(abs(loc_delta) / self.x_movement_enforce_rate) + 3

        last_teleport_x = None
        while True:
            dis = abs(self.x - goal_x)
            if dis <= self.horizontal_goal_offset:
                return True

            # skip shikigami if last teleport failed
            if abs(self.x - start_x) >= no_attack_distance and \
                    (last_teleport_x is None or abs(last_teleport_x-self.x) > self.horizontal_goal_offset):
                self.shikigami_haunting(False)

            if dis <= self.horizontal_movement_threshold:
                self.horizontal_move_goal(goal_x)
            else:
                last_teleport_x = self.x
                time.sleep(0.03)  # can teleport immediately after 3rd hit of shikigami haunting
                if loc_delta > 0:
                    self.teleport_left()
                else:
                    self.teleport_right()
                time.sleep(0.26)

            self.update()
            if time.time() - start_time > time_limit:
                return False

    def optimized_horizontal_move(self, goal_x):
        """
        Move from self.x to goal_x in as little time as possible. Uses multiple movement solutions for efficient paths.
        Blocking call. This function will stop moving after a time threshold is met and still haven't
        met the goal. Default threshold is 15 minimap pixels per second.
        :param goal_x: x coordinate to move to. This function only takes into account x coordinate movements.
        # :param ledge: If true, goal_x is an end of a platform, and additional movement solutions can be used. If not, precise movement is required.
        :return: None
        """
        loc_delta = self.x - goal_x
        abs_loc_delta = abs(loc_delta)
        start_time = time.time()
        time_limit = math.ceil(abs_loc_delta/self.x_movement_enforce_rate) + 3
        if loc_delta < 0:  # we need to move right
            if abs_loc_delta <= self.horizontal_movement_threshold:
                # Just walk if distance is less than threshold
                self.key_mgr.direct_press(DIK_RIGHT)

                # Below: use a loop to continuously press right until goal is reached or time is up
                while True:
                    if time.time()-start_time > time_limit:
                        break

                    self.update()
                    # Problem with synchonizing player_pos with self.x and self.y. Needs to get resolved.
                    # Current solution: Just call self.update() (not good for redundancy)
                    if self.x >= goal_x - self.horizontal_goal_offset:
                        # Reached or exceeded destination x coordinates
                        break

                self.key_mgr.direct_release(DIK_RIGHT)
            else:
                # Distance is quite big, so we teleport
                self.teleport_right()
                self.horizontal_move_goal(goal_x)
        elif loc_delta > 0:  # we are moving to the left
            if abs_loc_delta <= self.horizontal_movement_threshold:
                self.key_mgr.direct_press(DIK_LEFT)

                # Below: use a loop to continously press left until goal is reached or time is up
                while True:
                    if time.time()-start_time > time_limit:
                        break

                    self.update()
                    # Problem with synchonizing player_pos with self.x and self.y. Needs to get resolved.
                    # Current solution: Just call self.update() (not good for redundancy)
                    if self.x <= goal_x + self.horizontal_goal_offset:
                        # Reached or exceeded destination x coordinates
                        break

                self.key_mgr.direct_release(DIK_LEFT)
            else:
                # Distance is quite big, so we teleport
                self.teleport_left()
                self.horizontal_move_goal(goal_x)

    def horizontal_move_goal(self, goal_x):
        """
        Blocking call to move from current x position(self.x) to goal_x. Only counts x coordinates.
        Refactor notes: This function references self.screen_processor
        :param goal_x: goal x coordinates
        :return: None
        """
        dis = abs(self.x - goal_x)
        if dis <= self.horizontal_goal_offset:
            return True

        start_time = time.time()
        time_limit = math.ceil(dis / self.x_movement_enforce_rate) + 3
        right = goal_x - self.x > 0  # need to go right:

        self.key_mgr.direct_press(DIK_RIGHT if right else DIK_LEFT)
        while True:
            time.sleep(0.02)

            self.update()
            if not self.x:
                raise Exception("horizontal_move goal: failed to recognize coordinates")

            if abs(self.x - goal_x) <= self.horizontal_goal_offset:
                self.key_mgr.direct_release(DIK_RIGHT if right else DIK_LEFT)
                return True

            if time.time() - start_time > time_limit:
                self.key_mgr.direct_release(DIK_RIGHT if right else DIK_LEFT)
                return False

    def teleport_up(self):
        self._do_teleport(DIK_UP)

    def teleport_down(self):
        self._do_teleport(DIK_DOWN)

    def teleport_left(self):
        self._do_teleport(DIK_LEFT)

    def teleport_right(self):
        self._do_teleport(DIK_RIGHT)

    def _do_teleport(self, dir_key):
        """Warining: is a blocking call"""
        self.key_mgr.direct_press(dir_key)
        time.sleep(0.03)
        self.key_mgr.direct_press(self.keymap["teleport"])
        time.sleep(0.03 + abs(self.random_duration(0.05)))
        self.key_mgr.direct_release(dir_key)
        time.sleep(0.03)
        self.key_mgr.direct_release(self.keymap["teleport"])

    def shikigami_charm(self):
        self.key_mgr.single_press(self.keymap["shikigami_charm"])

    def jump(self):
        self.key_mgr.single_press(self.keymap["jump"])

    def jumpl(self):
        """Blocking call"""
        self.key_mgr.direct_press(DIK_LEFT)
        time.sleep(0.1)
        self.key_mgr.direct_press(self.keymap["jump"])
        time.sleep(0.1)
        self.key_mgr.direct_release(DIK_LEFT)
        time.sleep(0.04 + abs(self.random_duration(0.1)))
        self.key_mgr.direct_release(self.keymap["jump"])

    def jumpr(self):
        """Blocking call"""
        self.key_mgr.direct_press(DIK_RIGHT)
        time.sleep(0.1)
        self.key_mgr.direct_press(self.keymap["jump"])
        time.sleep(0.1)
        self.key_mgr.direct_release(DIK_RIGHT)
        time.sleep(0.04 + abs(self.random_duration(0.1)))
        self.key_mgr.direct_release(self.keymap["jump"])

    def drop(self):
        """Blocking call"""
        self.key_mgr.direct_press(DIK_DOWN)
        time.sleep(0.05 + abs(self.random_duration()))
        self.key_mgr.direct_press(self.keymap["jump"])
        time.sleep(0.05 + abs(self.random_duration()))
        self.key_mgr.direct_release(self.keymap["jump"])
        time.sleep(0.1 + abs(self.random_duration()))
        self.key_mgr.direct_release(DIK_DOWN)

    def shikigami_haunting(self, wait_delay=True):
        for _ in range(3):
            self.key_mgr.single_press(self.keymap["shikigami_haunting"])
            time.sleep(0.06 + abs(self.random_duration(0.005)))
        self.skill_cast_counter += 1
        if wait_delay:
            time.sleep(self.shikigami_haunting_delay)

    def exorcist_charm(self, wait_delay=True):
        self.key_mgr.single_press(self.keymap["exorcist_charm"])
        self.skill_cast_counter += 1
        if wait_delay:
            time.sleep(1.1 + abs(self.random_duration(0.01)))

    def kishin_shoukan(self):
        self._use_set_skill('kishin_shoukan')

    def yaksha_boss(self):
        self._use_set_skill('yaksha_boss')

    def nightmare_invite(self):
        self._use_set_skill('nightmare_invite')

    def _use_set_skill(self, skill_name):
        for _ in range(2):
            self.key_mgr.single_press(self.keymap[skill_name], duration=0.25, additional_duration=abs(self.random_duration(0.2)))
        self.last_skill_use_time[skill_name] = time.time()
        self.skill_cast_counter += 1
        time.sleep(self.set_skill_common_delay)

    def _use_buff_skill(self, skill_name, skill_cd, wait_before=0.0):
        if self.keymap.get(skill_name) is None:
            return False

        if time.time() - self.last_skill_use_time[skill_name] > skill_cd + random.randint(0, 6):
            if wait_before:
                time.sleep(wait_before)
            for _ in range(2):
                self.key_mgr.single_press(self.keymap[skill_name], duration=0.25)
                time.sleep(0.1)
            self.skill_cast_counter += 1
            self.last_skill_use_time[skill_name] = time.time()
            time.sleep(self.buff_common_delay)
            return True

        return False

    def holy_symbol(self, wait_before=0):
        return self._use_buff_skill('holy_symbol', self.v_buff_cd, wait_before)

    def speed_infusion(self, wait_before=0):
        return self._use_buff_skill('speed_infusion', self.v_buff_cd, wait_before)

    def mihaha_link(self, wait_before=0):
        return self._use_buff_skill('mihaha_link', self.v_buff_cd, wait_before)

    def haku_reborn(self, wait_before=0):
        return self._use_buff_skill('haku_reborn', 500, wait_before)

    def yuki_musume(self, wait_before=0):
        return self._use_buff_skill('yuki_musume', 75, wait_before)

    def is_on_platform(self, platform, offset=0):
        return (platform.start_y <= self.y <= platform.start_y + offset  # may being kicked by monster
                and (platform.start_x - offset) <= self.x <= (platform.end_x + offset))

    def random_duration(self, gen_range=0.1, digits=2):
        """
        returns a random number x where -gen_range<=x<=gen_range rounded to digits number of digits under floating points
        :param gen_range: float for generating number x where -gen_range<=x<=gen_range
        :param digits: n digits under floating point to round. 0 returns integer as float type
        :return: random number float
        """
        d = round(random.uniform(0, gen_range), digits)
        if random.choice([1,-1]) == -1:
            d *= -1
        return d
