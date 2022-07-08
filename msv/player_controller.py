import time, math, random
from msv.directinput_constants import DIK_RIGHT, DIK_DOWN, DIK_LEFT
from msv.input_manager import DEFAULT_KEY_MAP
from msv.screen_processor import MiniMapError
from msv.util import random_number


# simple jump vertical distance: about 6 pixels
class PlayerController:
    ROPE_CD = 3
    TELEPORT_HORIZONTAL_RANGE = 27
    SHIKIGAMI_HAUNTING_RANGE = 1
    SET_SKILL_COMMON_DELAY = 0.35
    BUFF_COMMON_DELAY = 0.7

    """
    This class keeps track of character location and manages advanced movement and attacks.
    """
    def __init__(self, key_mgr, screen_processor, keymap=DEFAULT_KEY_MAP):
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
        :param screen_processor: Handle to StaticImageProcessor. Only used to call find_player_minimap_marker

        Bot States:
        Idle
        ChangePlatform
        AttackinPlatform
        """
        self.x = self.y = None
        self.last_rope_time = 0

        self.keymap = keymap.copy()
        self.key_mgr = key_mgr
        self.screen_processor = screen_processor
        self.goal_x = self.goal_y = None

        self.busy = False

        self.horizontal_goal_offset = 2

        self.x_movement_enforce_rate = 15  # refer to optimized_horizontal_move

        self.horizontal_movement_threshold = 27  # teleport instead of walk if distance greater than threshold

        self.skill_cast_counter = 0
        self.skill_counter_time = 0

        self.skill_cooldown = {
             'blade_tornado': 9, 'blades_of_destiny': 8, 'final_cut': 83,
        }

        self.v_buff_cd = 180  # common cool down for v buff

        self.last_skill_use_time = {
            'final_cut': 0, 'blades_of_destiny': 0, 'holy_symbol': 0, 'blade_tornado': 0,
            'blade_clone': 0, 'goddess_blessing': 0, 'last_resort': 0, 'wild_totem': 0
        }

    def update(self, player_coords_x=None, player_coords_y=None):
        """
        Updates self.x, self.y to input coordinates
        :param player_coords_x: Coordinates to update self.x
        :param player_coords_y: Coordinates to update self.y
        :return: None
        """
        if player_coords_x:
            self.x, self.y = player_coords_x, player_coords_y
        else:
            self.screen_processor.update_image()
            pos = self.screen_processor.find_player_minimap_marker()
            if not pos:
                raise MiniMapError("failed to find player pos in minimap")
            self.x, self.y = pos

    def distance(self, coord1, coord2):
        return math.sqrt((coord1[0]-coord2[0])**2 + (coord1[1]-coord2[1])**2)

    def dbl_jump_move(self, goal_x, attack=False):
        """
        This function will, while moving towards goal_x, constantly use shikigami haunting and not overlapping
        X coordinate max error on flat surface: +- 5 pixels
        :param goal_x: minimap x goal coordinate.
        :param no_attack_distance: Distance in x pixels where any attack skill would not be used and just move
        """
        self.update()
        loc_delta = self.x - goal_x
        if abs(loc_delta) < self.horizontal_goal_offset:
            return True

        self.key_mgr.single_press(DIK_LEFT if loc_delta > 0 else DIK_RIGHT)  # turn to correct direction

        start_time = time.time()
        time_limit = math.ceil(abs(loc_delta) / self.x_movement_enforce_rate) + 3

        while True:
            dis = abs(self.x - goal_x)
            if dis <= self.horizontal_goal_offset:
                return True

            if dis <= self.horizontal_movement_threshold:
                self.horizontal_move_goal(goal_x)
            else:
                # can teleport immediately after 3rd hit of shikigami haunting
                if loc_delta > 0:
                    self.dbl_jump_left(attack=attack)
                else:
                    self.dbl_jump_right(attack=attack)

            self.update()
            if time.time() - start_time > time_limit:
                return False

    def horizontal_move_goal(self, goal_x, timeout=None, precise=False):
        """
        Blocking call to move from current x position(self.x) to goal_x. Only counts x coordinates.
        Refactor notes: This function references self.screen_processor
        :param goal_x: goal x coordinates
        :return: None
        """
        dis = abs(self.x - goal_x)
        if precise:
            offset = min(dis, self.horizontal_goal_offset)
            if offset == 0:
                return True
        else:
            offset = self.horizontal_goal_offset
            if dis <= offset:
                return True

        start_time = time.time()
        time_limit = timeout or math.ceil(dis / self.x_movement_enforce_rate) + 3
        right = goal_x - self.x > 0  # need to go right:

        self.key_mgr.direct_press(DIK_RIGHT if right else DIK_LEFT)
        while True:
            time.sleep(0.02)
            self.update()

            if (right and self.x >= goal_x - offset) or (not right and self.x <= goal_x + offset):
                self.key_mgr.direct_release(DIK_RIGHT if right else DIK_LEFT)
                return True

            if time.time() - start_time > time_limit:
                self.key_mgr.direct_release(DIK_RIGHT if right else DIK_LEFT)
                return False

    def stay(self, timeout, goal_x=None):
        start_time = time.time()

        while True:
            self.update()
            if goal_x is None:
                goal_x = self.x
                continue

            self.horizontal_move_goal(goal_x, time.time()-timeout)

            if time.time()-timeout > start_time:
                break

            time.sleep(0.02)

    def teleport_up(self):
        self.key_mgr.single_press(self.keymap["jump"])
        time.sleep(0.15 + random_number(0.02))
        self.key_mgr.single_press(self.keymap["blade_ascension"])
        self._wait_drop(True)

    def dbl_jump_left(self, third=False, jump=False, attack=False, wait=True):
        return self._do_dbl_jump(DIK_LEFT, third, jump, attack, wait)

    def dbl_jump_right(self, third=False, jump=False, attack=False, wait=True):
        return self._do_dbl_jump(DIK_RIGHT, third, jump, attack, wait)

    def _do_dbl_jump(self, dir_key, third, jump, attack, wait):
        """Warining: is a blocking call"""
        self.key_mgr.single_press(dir_key)
        time.sleep(0.03)
        self.key_mgr.single_press(self.keymap["jump"])
        time.sleep(0.15 + random_number(0.01))
        self.key_mgr.single_press(self.keymap["jump"])
        if third:
            time.sleep(0.16)
            self.key_mgr.single_press(self.keymap["jump"])
        if jump:
            time.sleep(0.16)
            self.key_mgr.single_press(self.keymap["blade_ascension"])
        elif attack:
            time.sleep(0.04)
            self.key_mgr.single_press(self.keymap["blade_fury"])

        if wait:
            if attack:
                time.sleep(0.49 + random_number(0.02))
            else:
                self._wait_drop(True)
        return True

    def rope_up(self, wait=True):
        elapsed = time.time() - self.last_rope_time
        if elapsed < self.ROPE_CD:
            self.stay(self.ROPE_CD - elapsed)
        self.key_mgr.single_press(self.keymap["rope"])
        self.last_rope_time = time.time()
        if wait:
            self._wait_drop(True)

    def shikigami_charm(self):
        self.key_mgr.single_press(self.keymap["shikigami_charm"])

    def jump(self):
        self.key_mgr.single_press(self.keymap["jump"])

    def jump_left(self, wait=True):
        """Blocking call"""
        self._do_jump(DIK_LEFT, wait)

    def jump_right(self, wait=True):
        """Blocking call"""
        self._do_jump(DIK_RIGHT, wait)

    def _do_jump(self, dir_key, wait):
        self.key_mgr.direct_press(dir_key)
        time.sleep(0.1)
        self.key_mgr.direct_press(self.keymap["jump"])
        time.sleep(0.1)
        self.key_mgr.direct_release(dir_key)
        time.sleep(0.04 + random_number(0.1))
        self.key_mgr.direct_release(self.keymap["jump"])
        if wait:
            self._wait_drop(True)

    def drop(self, wait=True):
        """Blocking call"""
        self.key_mgr.direct_press(DIK_DOWN)
        time.sleep(0.05 + random_number(0.08))
        self.key_mgr.direct_press(self.keymap["jump"])
        time.sleep(0.05 + random_number(0.08))
        self.key_mgr.direct_release(self.keymap["jump"])
        time.sleep(0.07 + random_number(0.08))
        self.key_mgr.direct_release(DIK_DOWN)
        if wait:
            self._wait_drop(False)

    def _wait_drop(self, wait_jump):
        """Wait until dropped to ground"""
        self.update()
        prev_y = highest_y = self.y
        prev_x = self.x
        eq_count = 0
        jumped = not wait_jump
        for _ in range(250):
            time.sleep(0.02)
            self.update()
            if abs(self.x - prev_x) > 3:  # horizontal dbl jump
                eq_count = 0
            if self.y == prev_y:
                if jumped:
                    eq_count += 1
                    if eq_count >= (9 if wait_jump else 5):
                        break
            elif self.y > prev_y:
                eq_count = 0
            else:
                if jumped and self.y > highest_y:  # hit by monster after dropped to ground
                    break
                else:
                    jumped = True
                    eq_count = 0
                if self.y < highest_y:
                    highest_y = self.y
            prev_y, prev_x = self.y, self.x

    def blade_tornado(self):
        self.key_mgr.single_press(self.keymap["blade_tornado"])
        self.skill_cast_counter += 1
        time.sleep(0.5 + random_number(0.05))

    def blade_fury(self):
        self.key_mgr.single_press(self.keymap["blade_fury"])
        self.skill_cast_counter += 1
        time.sleep(0.7 + random_number(0.05))

    def blades_of_destiny(self):
        self.key_mgr.single_press(self.keymap["blades_of_destiny"])
        self.skill_cast_counter += 1
        time.sleep(0.5 + random_number(0.05))

    def use_set_skill(self, skill_name):
        times = 1 if skill_name == 'dark_lord_omen' else 2
        for i in range(times):
            self.key_mgr.single_press(self.keymap[skill_name], duration=0.2 + random_number(0.04),
                                      additional_duration=0 if i == 1 else 0.36 + random_number(0.04))
        self.last_skill_use_time[skill_name] = time.time()
        self.skill_cast_counter += 1
        time.sleep(self.SET_SKILL_COMMON_DELAY + random_number(0.1))

        return True

    def is_skill_usable(self, skill_name):
        return (self.keymap.get(skill_name) is not None
                and time.time() - self.last_skill_use_time[skill_name] > self.skill_cooldown[skill_name])

    def _use_buff_skill(self, skill_name, skill_cd, wait_before=0.0, times=2):
        if self.keymap.get(skill_name) is None:
            return False

        if time.time() - self.last_skill_use_time[skill_name] > skill_cd + random.randint(0, 6):
            if wait_before:
                time.sleep(wait_before)
            for i in range(times):
                self.key_mgr.single_press(self.keymap[skill_name], additional_duration=0 if (times == 1 or i == 1) else 0.15 + random_number(0.04))
            self.skill_cast_counter += 1
            self.last_skill_use_time[skill_name] = time.time()
            time.sleep(self.BUFF_COMMON_DELAY + random_number(0.04))
            return True

        return False

    def holy_symbol(self, wait_before=0):
        return self._use_buff_skill('holy_symbol', self.v_buff_cd, wait_before)

    def final_cut(self, wait_before=0):
        return self._use_buff_skill('final_cut', self.skill_cooldown['final_cut'], wait_before)

    def blade_clone(self, wait_before=0):
        return self._use_buff_skill('blade_clone', 90, wait_before)

    def goddess_blessing(self, wait_before=0):
        return self._use_buff_skill('goddess_blessing', 180, wait_before)

    def wild_totem(self, wait_before=0):
        return self._use_buff_skill('wild_totem', 100, wait_before)

    def last_resort(self, wait_before=0):
        return self._use_buff_skill('last_resort', 75, wait_before, times=1)

    def is_on_platform(self, platform, offset=0):
        return ((platform.start_y-offset) <= self.y <= platform.start_y  # may being kicked by monster
                and (platform.start_x-offset) <= self.x <= (platform.end_x+offset))

    def is_skill_key_set(self, skill_name):
        return self.keymap.get(skill_name) is not None
