import time
import cv2
import numpy as np
from matplotlib import pyplot as plt

tpl = cv2.imread('../../msv/resources/template/monster/ascendion_tpl.png', cv2.IMREAD_GRAYSCALE)
tpl_alpha = cv2.imread('../../msv/resources/template/monster/ascendion_tpl.png', cv2.IMREAD_UNCHANGED)[:,:,3]

img = cv2.imread('../unittest_data/monster/dd.png', cv2.IMREAD_GRAYSCALE)
img_h, img_w = img.shape[:2]


t = time.perf_counter()
img = img[0:img_h-100,0:img_w//2]
res = cv2.matchTemplate(img, tpl, cv2.TM_SQDIFF_NORMED, mask=tpl_alpha)
loc = np.where(res <= 0.04)
print(len(np.where(res <= 0.04)[0]))
print(time.perf_counter() - t)

for pt in zip(*loc[::-1]):
    h, w = tpl.shape[:2]
    cv2.rectangle(img, pt, (pt[0] + w, pt[1] + h), (0, 0, 255), 2)

plt.plot(122)
plt.imshow(cv2.cvtColor(img, cv2.COLOR_GRAY2RGB))
plt.title('Detected'), plt.xticks([]), plt.yticks([])
plt.show()
