import time
import random
from msv.macro_script import MacroController
from msv.util import random_number
import msv.directinput_constants as dc


class TrainNoDest1(MacroController):
    X = 82

    def __init__(self, conn=None, config=None):
        super().__init__(conn, config)
        self.aoe_skills = ['death_trigger', 'nautilus_strike', 'ugly_bomb', 'target_lock', 'true_arachnid_reflection',
                           'bullet_barrage', 'nautilus_assault']

    def loop(self):
        """
        这个职业技能都是1分钟左右的，所以1分钟一个循环刚好
        放置一共有4个，分别是艾尔达光雨（️↓+技能键）炮船×2 炮台×1，炮船(1)分别放在地图右侧下层，地图右侧上两层靠艾尔达光雨(T)，地图左侧最上台子放炮台(2)
        人在地图中间偏左位置，放范围技能（键盘H E R Q W Shift）
        """
        ### Rune Detector
        self._rune_detect_solve()
        if not self.current_platform_hash:  # navigate failed, skip rest logic, go unstick fast
            return

        if self.player_manager.is_skill_usable('nightmare_invite'):
            if self.set_skills():
                self.player_manager.drop()
                return

        if self.current_platform_hash == '7c9ea34a':
            self.buff_skills()

            self.player_manager.horizontal_move_goal(self.X)

            for _ in range(2):
                random.shuffle(self.aoe_skills)
                for i in self.aoe_skills:
                    if not self.player_manager.is_skill_usable(i):
                        continue
                    if i == 'true_arachnid_reflection':
                        self.player_manager.use_set_skill(i)
                    else:
                        getattr(self.player_manager, i)()
                    time.sleep(0.8 + random_number(0.05))
                    break

                dir_ = random.choice((dc.DIK_LEFT, dc.DIK_RIGHT))
                self.keyhandler.single_press(dir_)
                self.player_manager.eight_legs_easton()
                time.sleep(random_number(0.08))
                self.keyhandler.single_press(dc.DIK_LEFT if dir_ == dc.DIK_RIGHT else dc.DIK_RIGHT)
                self.player_manager.eight_legs_easton()
        else:
            self.navigate_to_platform('7c9ea34a')

        # Finished
        return 0
