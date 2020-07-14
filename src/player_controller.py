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
        self.jump_key = self.keymap["jump"]
        self.teleport_key = self.keymap["teleport"]
        self.key_mgr = key_mgr
        self.screen_processor = screen_handler
        self.goal_x = self.goal_y = None

        self.busy = False

        self.horizontal_goal_offset = 2

        self.x_movement_enforce_rate = 15  # refer to optimized_horizontal_move

        self.shikigami_haunting_range = 18  # exceed: moonlight slash's estimalte x hitbox RADIUS in minimap coords.
        self.shikigami_haunting_delay = 0.5  # delay after using shikigami haunting where character is not movable

        self.horizontal_movement_threshold = 18-2  # teleport instead of walk if distance greater than threshold

        self.skill_cast_counter = 0
        self.skill_counter_time = 0

        self.last_yaksha_boss_time = 0
        self.yaksha_boss_cooldown = 35
        self.yaksha_boss_delay = 1.6

        self.last_kishin_shoukan_time = 0
        self.kishin_shoukan_cooldown = 70
        self.kishin_shoukan_delay = 1.6

        self.rune_cooldown = 15
        self.last_rune_solve_time = 0

        self.v_buff_cd = 180 + 1  # common cool down for v buff
        self.buff_common_delay = 2  # common delay for v buff

        self.last_holy_symbol_time = 0
        self.last_speed_infusion_time = 0
        self.last_haku_reborn_time = 0

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
        This function will, while moving towards goal_x, constantly use exceed: moonlight slash and not overlapping
        This function currently does not have an time enforce implementation, meaning it may fall into an infinite loop
        if player coordinates are not read correctly.
        X coordinate max error on flat surface: +- 5 pixels
        :param goal_x: minimap x goal coordinate.
        :param no_attack_distance: Distance in x pixels where any attack skill would not be used and just move
        """
        start_x = self.x
        loc_delta = self.x - goal_x
        abs_loc_delta = abs(loc_delta)

        if not no_attack_distance:
            self.key_mgr.single_press(DIK_LEFT if loc_delta > 0 else DIK_RIGHT)  # turn to right direction

        if loc_delta > 0:  # left movement
            if no_attack_distance and no_attack_distance < abs_loc_delta:
                self.optimized_horizontal_move(self.x-no_attack_distance+self.horizontal_goal_offset, teleport_once=True)

            self.update()
            loc_delta = self.x - goal_x
            abs_loc_delta = abs(loc_delta)
            if abs_loc_delta < self.horizontal_movement_threshold:
                if not no_attack_distance:
                    self.shikigami_haunting()
                self.horizontal_move_goal(goal_x)
            else:
                while True:
                    self.update()

                    if self.x <= goal_x + self.horizontal_goal_offset:
                        break

                    if abs(self.x - start_x) >= no_attack_distance:
                        self.shikigami_haunting()

                    if abs(self.x - goal_x) < self.shikigami_haunting_range:
                        self.optimized_horizontal_move(goal_x, teleport_once=True)
                    else:
                        self.optimized_horizontal_move(self.x - self.shikigami_haunting_range, teleport_once=True)
        elif loc_delta < 0:  # right movement
            if no_attack_distance and no_attack_distance < abs_loc_delta:
                self.optimized_horizontal_move(self.x+no_attack_distance-self.horizontal_goal_offset, teleport_once=True)
            self.update()
            loc_delta = self.x - goal_x
            abs_loc_delta = abs(loc_delta)
            if abs_loc_delta < self.horizontal_movement_threshold:
                if not no_attack_distance:
                    self.shikigami_haunting()
                self.horizontal_move_goal(goal_x)
            else:
                while True:
                    self.update()

                    if self.x >= goal_x - self.horizontal_goal_offset:
                        break

                    if abs(self.x - start_x) >= no_attack_distance:
                        self.shikigami_haunting()

                    if abs(goal_x - self.x) < self.shikigami_haunting_range:
                        self.optimized_horizontal_move(goal_x, teleport_once=True)
                    else:
                        self.optimized_horizontal_move(self.x + self.shikigami_haunting_range, teleport_once=True)

    def optimized_horizontal_move(self, goal_x, teleport_once=False, enforce_time=True):
        """
        Move from self.x to goal_x in as little time as possible. Uses multiple movement solutions for efficient paths. Blocking call
        :param goal_x: x coordinate to move to. This function only takes into account x coordinate movements.
        :param ledge: If true, goal_x is an end of a platform, and additional movement solutions can be used. If not, precise movement is required.
        :param enforce_time: If true, the function will stop moving after a time threshold is met and still haven't
        met the goal. Default threshold is 15 minimap pixels per second.
        :return: None
        """
        loc_delta = self.x - goal_x
        abs_loc_delta = abs(loc_delta)
        start_time = time.time()
        time_limit = math.ceil(abs_loc_delta/self.x_movement_enforce_rate)
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
                if not teleport_once:
                    self.horizontal_move_goal(goal_x)
        elif loc_delta > 0:  # we are moving to the left
            if abs_loc_delta <= self.horizontal_movement_threshold:
                # Just walk if distance is less than 10
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
                if not teleport_once:
                    self.horizontal_move_goal(goal_x)

    def horizontal_move_goal(self, goal_x):
        """
        Blocking call to move from current x position(self.x) to goal_x. Only counts x coordinates.
        Refactor notes: This function references self.screen_processor
        :param goal_x: goal x coordinates
        :return: None
        """
        current_x = self.x
        if goal_x - current_x > 0:  # need to go right:
            mode = "r"
        elif goal_x - current_x < 0:  # need to go left:
            mode = "l"
        else:
            return 0

        if mode == "r":
            # need to go right:
            self.key_mgr.direct_press(DIK_RIGHT)
        elif mode == "l":
            # need to go left:
            self.key_mgr.direct_press(DIK_LEFT)
        while True:
            self.update()
            if not self.x:
                assert 1 == 0, "horizontal_move goal: failed to recognize coordinates"

            if mode == "r":
                if self.x >= goal_x-self.horizontal_goal_offset:
                    self.key_mgr.direct_release(DIK_RIGHT)
                    break
            elif mode == "l":
                if self.x <= goal_x+self.horizontal_goal_offset:
                    self.key_mgr.direct_release(DIK_LEFT)
                    break

    def teleport_up(self):
        self._do_teleport(DIK_UP)

    def teleport_left(self):
        self._do_teleport(DIK_LEFT)

    def teleport_right(self):
        self._do_teleport(DIK_RIGHT)

    def _do_teleport(self, dir_key, retry_limit=2):
        """Warining: is a blocking call"""
        self.key_mgr.direct_press(dir_key)
        time.sleep(0.05)
        self.key_mgr.direct_press(self.teleport_key)
        time.sleep(0.04)
        self.key_mgr.direct_release(dir_key)
        time.sleep(abs(self.random_duration(0.1)))
        self.key_mgr.direct_release(self.teleport_key)

        if retry_limit == 0:
            return
        pos = (self.x, self.y)
        self.update()
        new_pos = (self.x, self.y)
        if abs(pos[0] - new_pos[0]) <= 2 and abs(pos[1] - new_pos[1]) <= 2:
            time.sleep(0.3)
            self._do_teleport(dir_key, retry_limit-1)

    def jumpl(self):
        """Blocking call"""
        self.key_mgr.direct_press(DIK_LEFT)
        time.sleep(0.1)
        self.key_mgr.direct_press(self.jump_key)
        time.sleep(0.1)
        self.key_mgr.direct_release(DIK_LEFT)
        time.sleep(0.04 + abs(self.random_duration(0.1)))
        self.key_mgr.direct_release(self.jump_key)

    def jumpr(self):
        """Blocking call"""
        self.key_mgr.direct_press(DIK_RIGHT)
        time.sleep(0.1)
        self.key_mgr.direct_press(self.jump_key)
        time.sleep(0.1)
        self.key_mgr.direct_release(DIK_RIGHT)
        time.sleep(0.04 + abs(self.random_duration(0.1)))
        self.key_mgr.direct_release(self.jump_key)

    def drop(self):
        """Blocking call"""
        self.key_mgr.direct_press(DIK_DOWN)
        time.sleep(0.05 + abs(self.random_duration()))
        self.key_mgr.direct_press(self.jump_key)
        time.sleep(0.05 + abs(self.random_duration()))
        self.key_mgr.direct_release(self.jump_key)
        time.sleep(0.1 + abs(self.random_duration()))
        self.key_mgr.direct_release(DIK_DOWN)

    def shikigami_haunting(self, wait_delay=True):
        for _ in range(4):
            self.key_mgr.single_press(self.keymap["shikigami_haunting"])
            time.sleep(0.05 + abs(self.random_duration(0.01)))
        self.skill_cast_counter += 1
        if wait_delay:
            time.sleep(self.shikigami_haunting_delay)

    def kishin_shoukan(self):
        self.key_mgr.single_press(self.keymap["kishin_shoukan"], duration=0.2, additional_duration=abs(self.random_duration()))
        self.last_kishin_shoukan_time = time.time()
        self.skill_cast_counter += 1
        time.sleep(self.kishin_shoukan_delay)

    def yaksha_boss(self):
        self.key_mgr.single_press(self.keymap["yaksha_boss"], duration=0.15, additional_duration=abs(self.random_duration()))
        self.last_yaksha_boss_time = time.time()
        self.skill_cast_counter += 1
        time.sleep(self.yaksha_boss_delay)

    def holy_symbol(self):
        if time.time() - self.last_holy_symbol_time > self.v_buff_cd + random.randint(0, 14):
            for _ in range(2):
                self.key_mgr.single_press(self.keymap["holy_symbol"], additional_duration=abs(self.random_duration()))
            self.skill_cast_counter += 1
            self.last_holy_symbol_time = time.time()
            time.sleep(self.buff_common_delay)

    def speed_infusion(self):
        if time.time() - self.last_speed_infusion_time > self.v_buff_cd + random.randint(0, 14):
            for _ in range(2):
                self.key_mgr.single_press(self.keymap["speed_infusion"], additional_duration=abs(self.random_duration()))
            self.skill_cast_counter += 1
            self.last_speed_infusion_time = time.time()
            time.sleep(self.buff_common_delay)

    def haku_reborn(self):
        if time.time() - self.last_haku_reborn_time > 500 + random.randint(0, 14):
            for _ in range(2):
                self.key_mgr.single_press(self.keymap["haku_reborn"], additional_duration=abs(self.random_duration()))
            self.skill_cast_counter += 1
            self.last_haku_reborn_time = time.time()
            time.sleep(self.buff_common_delay)

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
