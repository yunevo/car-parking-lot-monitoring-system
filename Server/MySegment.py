import cv2
import numpy as np
import matplotlib.pyplot as plt
from imutils import perspective
import imutils
from skimage import measure
from skimage.filters import threshold_local
import os

from DetectLP import return_coodinator

def convert2Square(image):
    """
    Resize non-square image(height != width to square one (height == width)
    :param image: input images
    :return: numpy array
    """

    img_h = image.shape[0]
    img_w = image.shape[1]

    # if height > width
    if img_h > img_w:
        diff = img_h - img_w
        if diff % 2 == 0:
            x1 = np.zeros(shape=(img_h, diff//2))
            x2 = x1
        else:
            x1 = np.zeros(shape=(img_h, diff//2))
            x2 = np.zeros(shape=(img_h, (diff//2) + 1))

        squared_image = np.concatenate((x1, image, x2), axis=1)
    elif img_w > img_h:
        diff = img_w - img_h
        if diff % 2 == 0:
            x1 = np.zeros(shape=(diff//2, img_w))
            x2 = x1
        else:
            x1 = np.zeros(shape=(diff//2, img_w))
            x2 = x1

        squared_image = np.concatenate((x1, image, x2), axis=0)
    else:
        squared_image = image

    return squared_image

def Segment(img):
    # crop number plate used by bird's eyes view transformation
    pts = return_coodinator(img)


    if len(pts) != 0:
        LpRegion = perspective.four_point_transform(img, pts)
        if LpRegion.shape[1] < 100 or LpRegion.shape[0] < 100:
            LpRegion = cv2.resize(LpRegion, (LpRegion.shape[1]*2, LpRegion.shape[0]*2))

        # V = cv2.split(cv2.cvtColor(LpRegion, cv2.COLOR_BGR2HSV))[2]
        # T = threshold_local(V, 15, offset=10, method="gaussian")
        # thresh1 = (V > T).astype("uint8") * 255
        gray = cv2.cvtColor(LpRegion, cv2.COLOR_BGR2GRAY)
        thresh1 = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
        # cv2.imshow("thresh", thresh1)
        # cv2.waitKey(0)

        # convert black pixel of digits to white pixel
        thresh = cv2.bitwise_not(thresh1)
        thresh = imutils.resize(thresh, width=400)
        thresh = cv2.medianBlur(thresh, 5)
        # connected components analysis
        labels = measure.label(thresh, connectivity=2, background=0)

        candidates = []
        # loop over the unique components
        for label in np.unique(labels):
           # if this is background label, ignore it
           if label == 0:
              continue

           # init mask to store the location of the character candidates
           mask = np.zeros(thresh.shape, dtype="uint8")
           mask[labels == label] = 255

           # find contours from mask
           contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

           if len(contours) > 0:
             contour = max(contours, key=cv2.contourArea)
             (x, y, w, h) = cv2.boundingRect(contour)
             # rule to determine characters
             aspectRatio = w / float(h)
             solidity = cv2.contourArea(contour) / float(w * h)
             heightRatio = h / float(LpRegion.shape[0])

             if 0.1 < aspectRatio < 1.0 and solidity > 0.1 and 0.35 < heightRatio < 2.0:
                 # extract characters
                 candidate = np.array(mask[y:y + h, x:x + w])
                 square_candidate = convert2Square(candidate)
                 square_candidate = cv2.resize(square_candidate, (28, 28), cv2.INTER_AREA)
                 square_candidate = square_candidate.reshape((28, 28, 1))
                 candidates.append((square_candidate, (y, x)))
    else:
        candidates = []
    return candidates, pts
"""
cv2.imshow("goc", img)
cv2.imshow("crop", LpRegion)
cv2.imshow("thresh", thresh)
plt.imshow(labels)
plt.show()
cv2.waitKey(0)
"""
# path = 'C:/Users/Acer/PycharmProjects/DoAnNKD/GreenParking/'
# FJoin = os.path.join
# files = [FJoin(path, f) for f in os.listdir(path)]
#
# for i in range(len(files)):
#     path = files[i]
#     img = cv2.imread(path)
#
#     candidates = Segment(img)
#
#     # round = str(i+1) + "_"
#     # round = "0_"
#     for i in range(len(candidates)):
#         cv2.imshow("candidates", candidates[i][0])
#         # if len(candidates) == 9:
#         #     if i == 2:
#         #         cv2.imwrite("./data/character/" + round + str(i) + ".png", candidates[i][0])
#         #     else:
#         #         cv2.imwrite("./data/digits/" + round + str(i) + ".png", candidates[i][0])
#         key = cv2.waitKey(0)
#         if key == 27:
#             break
