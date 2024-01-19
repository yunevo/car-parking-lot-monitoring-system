import cv2
import numpy as np
import matplotlib.pyplot as plt

def return_coodinator(image):
    # Load the YOLO Darknet model and the class names file
    net = cv2.dnn.readNetFromDarknet("./FileofNetRead/yolo-tinyv4-obg.cfg", "./FileofNetRead/yolo-tinyv4-obg_last.weights")
    # classes = []
    # with open("./FileofNetRead/obj.names", "r") as f:
    #     classes = [line.strip() for line in f.readlines()]
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

    # Load the image that contains the object you want to detect
    img = image

    # Get the dimensions of the image
    height, width, _ = img.shape

    # Set the confidence threshold for object detection
    conf_threshold = 0.5

    # Detect objects in the image
    blob = cv2.dnn.blobFromImage(img, 1/255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    # Loop through the detected objects and extract the bounding box coordinates
    class_ids = []
    boxes = []
    confidences = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > conf_threshold:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w/2)
                y = int(center_y - h/2)
                class_ids.append(class_id)
                confidences.append(float(confidence))
                boxes.append([x, y, w, h])
    # Apply non-maximum suppression to remove overlapping boxes
    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, 0.5)
    if len(indices) == 0:
        pts = []

    # Draw the bounding boxes around the detected objects
    for i in indices:
        i = i
        x, y, w, h = boxes[i]
        x2, y2 = x+w,y
        x3, y3 = x, y+h
        x4, y4 = x+w, y+h
        pts = np.float64([[x, y], [x2, y2], [x3, y3], [x4, y4]])
    return pts

# Display the image with the bounding boxes
# resized_image = cv2.resize(img, (int(width/2), int(height/2)), interpolation = cv2.INTER_CUBIC)
# print(img.shape)
# resized_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
# plt.figure(figsize=(20,10))
# plt.axis("off")
# plt.imshow(resized_image)
# plt.show()

# path_img = "C:/Users/Acer/Downloads/AnhTest5.jpg"
# img = cv2.imread(path_img)
# pts = return_coodinator(img)
# print(pts)
# cv2.imshow("Image", img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()