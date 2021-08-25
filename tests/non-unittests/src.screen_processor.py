import imutils, cv2, numpy as np, time
from msv.screen_processor import ScreenProcessor
from msv.screen_processor import StaticImageProcessor


screencap = ScreenProcessor()
scrp = StaticImageProcessor(screencap)
scrp.update_image()
area = scrp.get_minimap_rect()


while True:
    t = time.perf_counter()
    scrp.update_image(set_focus=False)
    playerpos = scrp.find_player_minimap_marker(area)
    print("regular", time.perf_counter() - t)
    time.sleep(0.02)

    regular_find = scrp.bgr_img[area[1]:area[1] + area[3], area[0]:area[0] + area[2]].copy()
    if playerpos:
        cv2.circle(regular_find, playerpos, 4, (255, 0, 0), -1)
        print(playerpos)
    regular_find = imutils.resize(regular_find, width=400)
    cv2.imshow("regular vs templ", regular_find)

    #print("regular", playerpos)
    #print("templ", playerpos_templ)

    inp = cv2.waitKey(1)
    if inp == ord("q"):
        cv2.destroyAllWindows()
        break

    elif inp == ord("r"):
        scrp.reset_minimap_area()
        area = scrp.get_minimap_rect()