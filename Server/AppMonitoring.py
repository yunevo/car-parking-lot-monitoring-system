import tkinter
from tkinter import messagebox
import cv2
import PIL.Image, PIL.ImageTk

import numpy as np
import paho.mqtt.client as mqtt

from Classification_Vid import Recog_LP
from Database.Database import *

NAME = "laptop"
PASS = "012345678"

class App:
     def __init__(self, window, window_title, video_source=0):
         self.window = window
         self.window.title(window_title)
         self.video_source = video_source
         self.old_source = 0

         # Khai bao message va LP_entry
         self.msg = ''
         self.LP = ''

         # open video source (by default this will try to open the computer webcam)
         self.vid = MyVideoCapture(self.video_source)
         self.window.geometry(str(int(self.vid.width)) + 'x' + str(int(self.vid.height)))

         # Khai bao img_LP va lince_plate
         self.img_LP = np.zeros((int(self.vid.height), int(self.vid.width)))
         self.license_plate = ''

         # Create a canvas that can fit the above video source size
         self.canvas1 = tkinter.Canvas(window, width = int(self.vid.width/2), height = int(self.vid.height/2))
         self.canvas1.place(x=0, y=0)

         self.canvas2 = tkinter.Canvas(window, width = int(self.vid.width/2), height = int(self.vid.height/2))
         self.canvas2.place(x=int(self.vid.width/2), y=0)
         # Button that lets the user take a Okay
         self.btn_yes = tkinter.Button(window, text="Okay", width=20, command=self.Yes)

         # Button that lets the user take a Nhap
         self.btn_no = tkinter.Button(window, text="Nhap", width=20, command=self.No)

         # Entry
         self.entry_LP = tkinter.Entry(window, bg='white', fg='black', bd=3, width=30)

         # Button that lets the user take a Enter
         self.btn_enter = tkinter.Button(window, text="Enter", width=20, command=self.Enter)

         # Button that open the IN barrier
         self.btn_IN = tkinter.Button(window, text="B_IN", width=20, command=self.IN)
         self.btn_IN.place(x=5, y=int(self.vid.height) - 30)

         # Button that open the IN barrier
         self.btn_OUT = tkinter.Button(window, text="B_OUT", width=20, command=self.OUT)
         self.btn_OUT.place(x=int(self.vid.width*3/4), y=int(self.vid.height) - 30)

         # After it is called once, the update method will be automatically called every delay milliseconds
         self.delay = 15
         # self.delay = cv2.waitKey(0)
         self.update()

         #MQTT message
         # This is the event handler method that receives the Mosquito messages

         # broker_address = "192.168.88.83" # Kenhouse
         # broker_address = "192.168.0.101" #Nha
         # broker_address = '192.168.135.236' #Pinel
         broker_address = '192.168.137.32'

         print("creating new instance")
         self.client = mqtt.Client()  # create new instance
         self.client.username_pw_set(NAME, PASS)
         self.client.on_message = self.on_message  # attach function to callback

         print("connecting to broker")
         self.client.connect(broker_address, 1883, keepalive=120)  # connect to broker

         print("Subscribing to topic", "snap")
         self.client.subscribe("snapshot")

         # Start the MQTT Mosquito process loop
         self.client.loop_start()

         self.window.mainloop()

     def on_message(self, client, userdata, message):
         # An het cac button và entry
         self.entry_LP.place_forget()
         self.btn_enter.place_forget()

         # <mathe>_<in/out> mathe=4 chu
         self.msg = str(message.payload.decode("utf-8"))
         if len(self.msg[1:]) < 10:
             n = 10 - len(self.msg[1:])
             self.msg = self.msg[0] + n*'0' + self.msg[1:]
         print("message received ", self.msg[1:])

         if self.msg[0] == 'I':
            self.video_source = 0
            if self.video_source != self.old_source:
                self.vid = MyVideoCapture(self.video_source)
                self.old_source = self.video_source

         else:
            self.video_source = 1
            if self.video_source != self.old_source:
                self.vid = MyVideoCapture(self.video_source)
                self.old_source = self.video_source

         self.snapshot()

         # Hien thi yes/no
         # self.btn_yes.pack( padx= 1, pady= 10,  expand=True) #anchor=tkinter.SW,
         # self.btn_no.pack( padx= 1, pady= 1,  expand=True)
         self.btn_yes.place(x=int(self.vid.width / 8), y=int(self.vid.height/2)+10)
         self.btn_no.place(x=int(self.vid.width / 2)+int(self.vid.width / 8), y=int(self.vid.height/2)+10)

     def Yes(self):
         print('yes')
         # Tach message
         CARD_ID = self.msg[1:]
         DIR = self.msg[0]
         # Kiem tra chieu
         match DIR: #chinh lai lay thanh bien DIR
             case 'I':
                 print('xe dang vao')
                 # Neu vao thi luu vao database publish thanh cong
                 DB_insert_car_in(CARD_ID, self.license_plate, self.img_LP)
                 self.client.publish('barrier', 'IN')
                 messagebox.showinfo('SUCCESS', 'Vehicle with: \n + license plate: '+str(self.license_plate)+'\n + carded : '+str(CARD_ID)+'\nIN successfully.')
             case 'O':
                 # Neu ra
                 # kiem tra khop:
                 result = check_license_plate(self.license_plate, CARD_ID)
                 if result:
                     print('xe dang ra')
                     # Neu khop cap nhat database, publish thanh cong
                     DB_update_car_out(result, CARD_ID, self.img_LP)
                     self.client.publish('barrier', 'OUT')
                     messagebox.showinfo('SUCCESS', 'Vehicle with: \n + license plate: '+str(self.license_plate)+'\n + carded : '+str(CARD_ID)+'\nOUT successfully.')
                 else:
                     # Khong khop thong bao, publish ko thanh cong
                     messagebox.showerror("Error","License plate and card id don't match!")
                     # print( 'num_plate:', self.license_plate, 'card_id:', CARD_ID)
                     img2check = DB_get_image_in_from_card(CARD_ID)
                     if img2check != None:
                         img = cv2.imread(img2check)
                         cv2.imshow(CARD_ID, img)
                     else:
                         messagebox.showerror("Error", "Don't have license plate and card id!")

         self.btn_yes.place_forget()
         self.btn_no.place_forget()

     def No(self):
         self.btn_yes.place_forget()
         self.btn_no.place_forget()
         print('no')
         # Lam hien text box
         self.entry_LP.place(x=int(self.vid.width / 4), y=int(self.vid.height/2)+10)
         self.btn_enter.place(x=int(self.vid.width / 2)+30, y=int(self.vid.height/2)+8)

     def Enter(self):
         self.LP = self.entry_LP.get()
         print(self.LP)
         # Tach message
         CARD_ID = self.msg[1:]
         DIR = self.msg[0]
         if self.LP != '':
             match DIR:  # chinh lai lay thanh bien DIR
                 case 'I':
                     print('xe dang vao')
                     # Neu vao thi luu vao database publish thanh cong
                     DB_insert_car_in(CARD_ID, self.LP, self.img_LP)
                     self.client.publish('barrier', 'IN')
                     messagebox.showinfo('SUCCESS', 'Vehicle with: \n + license plate: '+str(self.LP)+'\n + carded : '+str(CARD_ID)+'\nIN successfully.')
                 case 'O':
                     print('xe dang ra')
                     # Neu ra
                     # kiem tra khop:
                     result = check_license_plate(self.LP, CARD_ID)
                     if result:
                         # Neu khop cap nhat database, publish thanh cong
                         DB_update_car_out(result, CARD_ID, self.img_LP)
                         self.client.publish('barrier', 'OUT')
                         messagebox.showinfo('SUCCESS', 'Vehicle with: \n + license plate: '+str(self.LP)+'\n + carded : '+str(CARD_ID)+'\nOUT successfully.')
                     else:
                         # Khong khop thong bao, publish ko thanh cong
                         messagebox.showerror("Error", "License plate and card id don't match!")
                         img2check = DB_get_image_in_from_card(CARD_ID)
                         if img2check != None:
                             img = cv2.imread(img2check)
                             cv2.imshow(CARD_ID, img)
                         else:
                             messagebox.showerror("Error", "Don't have license plate and card id!")

         # self.No()
         # làm sao để xóa nội dung trong entry sau khi nhập
         self.entry_LP.place_forget()
         self.btn_enter.place_forget()
         self.btn_yes.place_forget()
         self.btn_no.place_forget()

     def IN(self):
         self.client.publish('barrier', 'IN')

     def OUT(self):
         self.client.publish('barrier', 'OUT')

     def snapshot(self):
         # Get a frame from the video source
         ret, frame = self.vid.get_frame()

         # self.RegLP = 1
         print('Taking a picture')
         self.img_LP, self.license_plate = Recog_LP(frame)

         if ret:
             # cv2.imwrite("./screenshot/frame-" + time.strftime("%d-%m-%Y-%H-%M-%S") + ".jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
             self.photo1 = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(self.img_LP))
             self.canvas2.create_image(int(self.vid.width/2), 0, image=self.photo1, anchor=tkinter.NE)


     def update(self):
         # Get a frame from the video source
         ret, frame = self.vid.get_frame()

         if ret:
             self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(frame))
             self.canvas1.create_image(0, 0, image = self.photo, anchor = tkinter.NW)

         self.window.after(self.delay, self.update)


class MyVideoCapture:
     def __init__(self, video_source=0):
         # Open the video source
         self.vid = cv2.VideoCapture(video_source)
         if not self.vid.isOpened():
             raise ValueError("Unable to open video source", video_source)

         # Get video source width and height
         self.width = self.vid.get(cv2.CAP_PROP_FRAME_WIDTH)
         self.height = self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT)

     def get_frame(self):
         ret, frame = self.vid.read()
         if self.vid.isOpened():
             if ret:
                 frame = cv2.resize(frame, (int(frame.shape[1]/2), int(frame.shape[0]/2)))
                 # Return a boolean success flag and the current frame converted to BGR
                 return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
             else:
                 return (ret, None)
         else:
             return (ret, None)

     # Release the video source when the object is destroyed
     def __del__(self):
         if self.vid.isOpened():
             self.vid.release()

# Create a window and pass it to the Application object
App(tkinter.Tk(), "Tkinter and OpenCV")
