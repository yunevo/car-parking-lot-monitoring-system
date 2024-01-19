import paho.mqtt.client as mqttc
import mysql.connector
import datetime
import cv2 as cv


#MQTT

# IP = "172.17.38.105"
#
# def on_connect(client, userdata, flags, rc):
#     print("Connected with result code " + str(rc))
#     client.subscribe("ThongBaoLoi")
#
#
# def on_message(client, userdata, msg):
#     print(msg.topic + " " + msg.payload.decode('utf-8'))
#
#
# client = mqttc.Client(client_id="", clean_session=True, transport="tcp")
# client.username_pw_set("laptop", "Tra20kRoiVao")
#
#
# client.on_connect = on_connect
# client.on_message = on_message
#
#
# client.connect(IP, 1883, keepalive=120)
# client.loop_start()
#
# def send_message(Topic, Message):
#     client.publish("Loi", "OK")
#
#
# send_message("01020", "OK")
#SQL

mydb = mysql.connector.connect(
    host = "localhost",
    user = "root",
    passwd = "12345678",
    database = "CAR_PARKING"
)


# Get cursor
mycursor = mydb.cursor()




def DB_insert(table, data, num_of_param):
    mycursor.execute("INSERT INTO " + str(table) + " VALUES (" + "%s,"*(num_of_param-1) + "%s" + ")",data)
    mydb.commit()
    print('correct')


def get_today_order():
    mycursor.execute("SELECT COUNT(PARKINGID) FROM PARKING WHERE DATE(TIMEIN) = %s", (datetime.datetime.now().date(),))
    results = mycursor.fetchall()
    return int(results[0][0])


def DB_insert_car_in(card_id, number_plate, img):
    now = datetime.datetime.now()
    global order
    order += 1
    parking_id = today_id +"_"+str(order)
    image_name = "./images/in_" + parking_id + ".jpg"
    cv.imwrite(image_name, img)
    print( 'park_id:' , parking_id , 'num_plate:', number_plate , 'card_id:', card_id , 'img_name: ', image_name)
    mycursor.execute("UPDATE CARD SET INUSE = %s WHERE CARDID = %s", ("USE", card_id))
    DB_insert("PARKING",(parking_id,number_plate,card_id,now, None,image_name,None,"PARKING"), 8)



def check_license_plate(license_plate, card_id):
    mycursor.execute("SELECT PARKINGID FROM PARKING WHERE NUMBERPLATE = %s AND CARDID = %s AND TIMEOUT IS NULL ORDER BY TIMEOUT DESC LIMIT 1",(license_plate, card_id))
    parking_id = mycursor.fetchall()
    print('parking_id to compare: ', parking_id)
    if parking_id:
        return parking_id[0][0]
    return False

def DB_update_car_out(parking_id, card_id, image):
    image_name = "./images/out_" + parking_id + ".jpg"
    cv.imwrite(image_name, image)
    now = datetime.datetime.now()
    mycursor.execute("UPDATE PARKING SET TIMEOUT = %s, IMAGEOUT = %s, STATE = %s WHERE PARKINGID = %s", (now, image_name, "DONE", parking_id))
    mycursor.execute("UPDATE CARD SET INUSE = %s WHERE CARDID = %s",("NOTUSE",card_id))
    mydb.commit()


def DB_get_image_in_from_card(card_id):
    mycursor.execute("SELECT IMAGEIN FROM PARKING WHERE CARDID = %s AND TIMEOUT IS NULL ORDER BY TIMEOUT DESC LIMIT 1", (card_id,))
    results = mycursor.fetchall()
    if results:
        return results[0][0]
    else:
        return None

now = datetime.datetime.now()
#date part for parking id
today_id = now.today().strftime("%y%m%d")

#order part for parking id
order = get_today_order()




# image = cv.imread("car_images/Cars0.png")
#
# DB_insert_car_in("0011223355","123489", image)

# results = mycursor.fetchall()
# results = check_license_plate("123456", "0011223344")
# print(results)
#
# DB_update_car_out("230708_7","0011223344",image)







