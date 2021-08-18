# -*- coding:utf-8 -*-
from screen_processor import ScreenProcessor, StaticImageProcessor
import cv2, imutils, time
import numpy as np
cap = ScreenProcessor()
ct = StaticImageProcessor(cap)
from win32gui import SetForegroundWindow
while True:
    img = cap.capture()
    img_arr = img_arr[ct.default_minimap_scan_area[1]:ct.default_minimap_scan_area[3], ct.default_minimap_scan_area[0]:ct.default_minimap_scan_area[2]]
    #grayscale = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    #blurred = cv2.GaussianBlur(grayscale, (7,7), 5)
    #eroded = cv2.erode(blurred, (7,7))
    #dilated = cv2.dilate(eroded, (7,7))
    #canny = cv2.Canny(eroded, threshold1=210, threshold2=255)
    #canny = imutils.resize(dilated, width = 500)
    final_img = img_arr

    cv2.imshow("", imutils.resize(final_img, width=400))

    inp = cv2.waitKey(1)
    if inp == ord("q"):
        cv2.destroyAllWindows()
        break
    elif inp == ord("c"):
        SetForegroundWindow(cap.get_game_hwnd())
        time.sleep(1)
        ds = cap.capture()

        cv2.imwrite("output.png", ds)