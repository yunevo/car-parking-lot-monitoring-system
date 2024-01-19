import cv2
import numpy as np
import time
import os
from pynput.keyboard import Key, Controller

from keras import optimizers
from keras.layers import Dense, Conv2D, MaxPooling2D, Dropout, Flatten
from keras.models import Sequential

from MySegment import Segment

ALPHA_DICT = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E', 5: 'F', 6: 'G', 7: 'H', 8: 'K', 9: 'L', 10: 'M', 11: 'N', 12: 'P',
              13: 'R', 14: 'S', 15: 'T', 16: 'U', 17: 'V', 18: 'X', 19: 'Y', 20: 'Z', 21: '0', 22: '1', 23: '2', 24: '3',
              25: '4', 26: '5', 27: '6', 28: '7', 29: '8', 30: '9', 31: "Background"}

CHAR_CLASSIFICATION_WEIGHTS = "./FileofNetRead/weight.h5"

def Find_plates(candidates):
    # Cai dat model
    model = Sequential()
    model.add(Conv2D(32, (3, 3), padding='same', activation='relu', input_shape=(28, 28, 1)))
    model.add(Conv2D(32, (3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    model.add(Conv2D(64, (3, 3), padding='same', activation='relu'))
    model.add(Conv2D(64, (3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    model.add(Conv2D(64, (3, 3), padding='same', activation='relu'))
    model.add(Conv2D(64, (3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    model.add(Flatten())
    model.add(Dense(512, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(32, activation='softmax'))

    # Compile model, chỉ rõ hàm loss_function nào được sử dụng, phương thức đùng để tối ưu hàm loss function.
    model.compile(loss="categorical_crossentropy", optimizer=optimizers.Adam(1e-3), metrics=['acc'])

    # Load model da training
    model.load_weights(CHAR_CLASSIFICATION_WEIGHTS)

    characters = []
    coordinates = []
    for char, coord in candidates:
        characters.append(char)
        coordinates.append(coord)
        # cv2.imshow("Image", char)
        # cv2.waitKey(0)

    # characters = cv2.cvtColor(characters, cv2.COLOR_BGR2GRAY) #dung để test riêng khối classification
    characters = np.array(characters)
    result = model.predict_on_batch(characters)  # khi test riêng dùng .reshape(1,28,28,1) cho characters
    result_idx = np.uint8(np.argmax(result, axis=1))

    plates = []
    for i in range(len(result_idx)):
        if result_idx[i] == 31:  # if is background or noise, ignore it
            continue
        plates.append((ALPHA_DICT[result_idx[i]], coordinates[i]))
    return plates

def format(candidates, mess):
    first_line = []
    second_line = []

    for candidate, coordinate in candidates:
        if candidates[0][1][0] + 40 > coordinate[0]:
            first_line.append((candidate, coordinate[1]))
        else:
            second_line.append((candidate, coordinate[1]))

    # def take_second(s):
    #     return s[1]

    first_line = sorted(first_line, key=lambda x:x[1])
    second_line = sorted(second_line, key=lambda x:x[1])

    if len(second_line) == 0:  # if license plate has 1 line
        license_plate = "".join([str(ele[0]) for ele in first_line])
        if len(license_plate) < 8 or len(license_plate) > 10:
            mess = 'error'
            return '', mess
    else:  # if license plate has 2 lines
        license_plate = "".join([str(ele[0]) for ele in first_line]) + "_" + "".join([str(ele[0]) for ele in second_line])
        if len(license_plate) < 9 or len(license_plate) > 10:
            mess = 'error'
            return '', mess

    # print(license_plate)
    if ord(license_plate[2]) == 56:
        license_plate = license_plate.replace(license_plate[2], 'B', 1)
    elif ord(license_plate[2]) == 48:
        license_plate = license_plate.replace(license_plate[2], 'D', 1)
    if ord(license_plate[2]) < 65 or ord(license_plate[2]) > 90:
        mess = 'error'

    return license_plate, mess

def Recog_LP(img):
    start = time.time()

    candidates, pts = Segment(img)
    # print(len(candidates))

    if len(candidates) != 0:
        plates = Find_plates(candidates)

        err = "ok"
        license_plate, mess = format(plates, err)
        print(license_plate, mess)

        if mess == 'error':
            drawshow_LP(img, pts, mess)
            # cv2.waitKey(5000)
        else:
            drawshow_LP(img, pts, license_plate)

        end = time.time()
        print('Chuong trinh hoan thanh trong %.2f s' % (end - start))
    else:
        img = img
        license_plate = ''
    return img, license_plate

def drawshow_LP(img, pts, mess):
    x, y, x3, y3, x4, y4 = int(pts[0][0]), int(pts[0][1]), int(pts[2][0]), int(pts[2][1]), int(pts[3][0]), int(pts[3][1])
    cv2.rectangle(img, (x, y), (x4, y4), (0, 255, 0), 2)
    cv2.putText(img, mess, (x3, y3 + int((y3 - y) / 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    return img

# if __name__ == '__main__':
#     # path_img = "C:/Users/Acer/Downloads/AnhTest5.jpg"
#     # img = cv2.imread(path_img)
#
#     path = 'C:/Users/Acer/PycharmProjects/DoAnNKD/GreenParking/'
#     FJoin = os.path.join
#     files = [FJoin(path, f) for f in os.listdir(path)]
#
#     vid = cv2.VideoCapture(0)
#
#     snap = 0
#     # for i in range(len(files)):
#     while(vid.isOpened()):
#         # path = files[i]
#         # img = cv2.imread(path)
#
#         snap += 1
#         _, img = vid.read()
#
#         keyboard = Controller()
#         if snap == 10:
#             keyboard.press(Key.space)
#
#         if snap == 50:
#             keyboard.press(Key.esc)
#
#         print(snap)
#
#         cv2.imshow("Image", img)
#         key = cv2.waitKey(1)
#         if key % 256 == 27:
#             # ESC pressed
#             print("Escape hit, closing...")
#             break
#         elif key % 256 == 32:
#             # SPACE pressed
#             print('One photo taken')
#             img = Recog_LP(img)
#             cv2.imshow("Image", img)
#             # keyboard.press(Key.space)
#             if cv2.waitKey(0):
#                 continue
#
#     vid.release()
#     cv2.destroyAllWindows()
