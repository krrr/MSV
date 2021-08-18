# -*- coding:utf-8 -*-
from screen_processor import ScreenProcessor
from input_manager import InputManager
from directinput_constants import DIK_SPACE, DIK_UP
import cv2, os, time, glob, imutils
cap = ScreenProcessor()
kbd = InputManager()
from win32gui import SetForegroundWindow
os.chdir("images/screenshots")
imgs = glob.glob("*.png")
highest = 0
for name in imgs:
    order = int(name[6:].split(".")[0])
    highest = max(order, highest)

x, y, w, h = 450, 180, 500, 130
while True:
    img_arr = cap.capture()
    final_img = imutils.resize(img_arr, width=200)
    cv2.imshow("s to automatically save 3 images in a row, d for just one", final_img)
    inp = cv2.waitKey(1)
    if inp == ord("q"):
        cv2.destroyAllWindows()
        break
    elif inp == ord("s"):
        SetForegroundWindow(cap.get_game_hwnd())
        for t in range(5):
            time.sleep(1)
            kbd.single_press(DIK_SPACE)
            time.sleep(0.3)
            ds = cap.capture()
            ds = ds[y:y+h, x:x+w]
            ds = cv2.cvtColor(ds, cv2.COLOR_BGR2HSV)
            # Maximize saturation
            ds[:, :, 1] = 255
            ds[:, :, 2] = 255
            ds = cv2.cvtColor(ds, cv2.COLOR_HSV2BGR)
            ds = cv2.cvtColor(ds, cv2.COLOR_BGR2GRAY)
            highest = highest + 1
            cv2.imwrite("output%d.png"%(highest), ds)
            print("saved", "output%d.png"%(highest))
            for g in range(3):
                kbd.single_press(DIK_UP)
                time.sleep(0.2)
            time.sleep(3)
        print("done")
    elif inp == ord("d"):
        SetForegroundWindow(cap.get_game_hwnd())
        time.sleep(0.3)
        ds = cap.capture()
        ds = ds[y:y + h, x:x + w]
        ds = cv2.cvtColor(ds, cv2.COLOR_BGR2HSV)
        # Maximize saturation
        ds[:, :, 1] = 255
        ds[:, :, 2] = 255
        ds = cv2.cvtColor(ds, cv2.COLOR_HSV2BGR)
        ds = cv2.cvtColor(ds, cv2.COLOR_BGR2GRAY)
        highest = highest + 1
        cv2.imwrite("output%d.png" % (highest), ds)
        print("saved", "output%d.png" % (highest))