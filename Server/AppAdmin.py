import cv2
import mysql.connector
import datetime
import tkinter
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox

mydb = mysql.connector.connect(
    host = "localhost",
    user = "root",
    passwd = "12345678",
    database = "CAR_PARKING"
)

mycursor = mydb.cursor()

def get_date_order(date):
    mycursor.execute("SELECT COUNT(PARKINGID) FROM PARKING WHERE DATE(TIMEIN) = %s", (date.date(),))
    results = mycursor.fetchall()
    return int(results[0][0])



# Get cursor
mycursor = mydb.cursor()

def DB_insert(table, data, num_of_param):
    mycursor.execute("INSERT INTO " + str(table) + " VALUES (" + "%s,"*(num_of_param-1) + "%s" + ")",data)
    mydb.commit()

def DB_get_parking_list(parking_id):
    mycursor.execute("SELECT * FROM PARKING WHERE PARKINGID LIKE %s ORDER BY TIMEIN DESC", (parking_id,))
    results = mycursor.fetchall()
    return results

def DB_get_PList_fromCardID(card_id):
    mycursor.execute("SELECT * FROM PARKING WHERE CARDID LIKE %s ORDER BY TIMEIN DESC", (card_id,))
    results = mycursor.fetchall()
    return results

def DB_get_PList_fromLP(license_plate):
    mycursor.execute("SELECT * FROM PARKING WHERE NUMBERPLATE LIKE %s ORDER BY TIMEIN DESC", (license_plate,))
    results = mycursor.fetchall()
    return results

def DB_get_PList_fromParkID_and_CardID(parking_id, card_id):
    mycursor.execute("SELECT * FROM PARKING WHERE PARKINGID LIKE %s AND CARDID LIKE %s ORDER BY TIMEIN DESC", (parking_id, card_id,))
    results = mycursor.fetchall()
    return results

def DB_update_parking(parking_id, number_plate, card_id, time_in, time_out, state):
    # remove space and new line character
    parking_id = parking_id.replace(' ', '').replace('\n','')
    number_plate = number_plate.replace(' ', '').replace('\n', '')
    card_id = card_id.replace(' ', '').replace('\n', '')
    time_in = time_in.replace(' ', '').replace('\n', '')
    time_out = time_out.replace(' ', '').replace('\n', '')
    # convert string to datetime for time column
    format = "%Y/%m/%d-%H:%M:%S"
    # assign empty string with None
    if number_plate == '':
        number_plate = None
    if card_id == '':
        card_id = None
    if time_in == '':
        time_in = None
    else:
        time_in = datetime.datetime.strptime(time_in, format)
    if time_out == '':
        time_out = None
    else:
        time_out = datetime.datetime.strptime(time_out, format)
    if state == '':
        state = None

    print(card_id)
    # Insert new row instead of update
    if parking_id == "_":
        date_id = time_in.strftime("%y%m%d")
        parking_id = date_id + "_" + str(get_date_order(time_in)+1)
        DB_insert("PARKING",(parking_id, number_plate, card_id, time_in, time_out, None, None, state), 8)
        return "ok"

    # Check if parking id valid
    mycursor.execute("SELECT * FROM PARKING WHERE PARKINGID LIKE %s", (parking_id,))
    results = mycursor.fetchall()
    if results:
        # if parking id is valid, update content
        mycursor.execute("UPDATE PARKING SET NUMBERPLATE = IFNULL(%s, NUMBERPLATE), CARDID = IFNULL(%s, CARDID), \
                            TIMEIN = IFNULL(%s, TIMEIN), TIMEOUT = IFNULL(%s, TIMEOUT), \
                            STATE = IFNULL(%s, STATE) WHERE PARKINGID LIKE %s",
                         (number_plate, card_id, time_in, time_out, state, parking_id))
        mydb.commit()
        return "ok"
    else:
        return "err"




def DB_delete_parking(parking_id):
    mycursor.execute("DELETE FROM PARKING WHERE PARKINGID LIKE %s", (parking_id,))
    mydb.commit()



# DB_update_parking("_", "79V1_12345", '0011223344', "2023/05/07-07:05:00", "2023/05/08-08:05:56", "DONE")
# DB_update_parking("230709_1%", "79V1_03345", '0011223344', "2023/05/07-07:05:00", "2023/05/08-08:05:56", "DONE")
# DB_delete_parking('230507%')
# print(DB_get_parking_list("230708%"))


# ______________________________________________

root = Tk()

root.title("Database Query")
root.geometry("1000x600")
file_location = ""
def click_search():
    parking_id = entry_parking_id.get()
    card_id = entry_card_id.get()
    license_plate = entry_license_plate.get()
    if parking_id != '' and card_id != '':
        results = DB_get_PList_fromParkID_and_CardID(parking_id, card_id)
    elif parking_id != '':
        results = DB_get_parking_list(parking_id)
    elif card_id != '':
        results = DB_get_PList_fromCardID(card_id)
    elif license_plate != '':
        results = DB_get_PList_fromLP(license_plate)

    show = Toplevel(root)
    show.geometry("400x530")
    show.title("Query Results")

    # create style for treeview
    style = ttk.Style()
    style.theme_use("clam")
    style.configure('Treeview', rowheight=30, font=['Courier', 10, 'bold'])
    style.configure('Treeview.Heading', rowheight=30, font=['Courier', 12, 'bold'])

    # create treeview frame
    tree_frame = Frame(show)
    tree_frame.pack(pady=10)

    # vertical scrollbar
    yscrollbar = ttk.Scrollbar(tree_frame)
    yscrollbar.pack(side=RIGHT, fill=Y)

    # create treeview
    tree = ttk.Treeview(tree_frame, height="15", yscrollcommand=yscrollbar.set)

    # configure scrollbar
    yscrollbar.config(command=tree.yview)

    # insert tree columns
    tree['columns'] = ("PARKINGID","NUMBERPLATE","CARDID","TIMEIN","TIMEOUT","IMAGEIN","IMAGEOUT","STATE")

    tree["displaycolumns"] = ("PARKINGID","NUMBERPLATE","CARDID","TIMEIN","TIMEOUT","IMAGEIN","IMAGEOUT","STATE")
    tree.column("#0", width=60, anchor=CENTER)
    tree.column("PARKINGID", width=100, anchor=CENTER)
    tree.column("NUMBERPLATE", width=120, anchor=CENTER)
    tree.column("CARDID", width=100, anchor=CENTER)
    tree.column("TIMEIN", width=170, anchor=CENTER)
    tree.column("TIMEOUT", width=170, anchor=CENTER)
    tree.column("IMAGEIN", width=200, anchor=CENTER)
    tree.column("IMAGEOUT", width=200, anchor=CENTER)
    tree.column("STATE", width=100, anchor=CENTER)

    tree.heading("#0", text="ORDER", anchor=CENTER)
    tree.heading("PARKINGID", text="PARKINGID", anchor=CENTER)
    tree.heading("NUMBERPLATE", text="NUMBERPLATE", anchor=CENTER)
    tree.heading("CARDID", text="CARDID", anchor=CENTER)
    tree.heading("TIMEIN", text="TIMEIN", anchor=CENTER)
    tree.heading("TIMEOUT", text="TIMEOUT", anchor=CENTER)
    tree.heading("IMAGEIN", text="IMAGEIN", anchor=CENTER)
    tree.heading("IMAGEOUT", text="IMAGEOUT", anchor=CENTER)
    tree.heading("STATE", text="STATE", anchor=CENTER)

    # tag configure
    tree.tag_configure("white", background="white")
    tree.tag_configure("gray", background="lightgray")

    # insert data
    for count, values in enumerate(results):
        if (count % 2 == 0):
            tree.insert(parent='', index='end', text=count+1, iid=count+1, values=values, tag="white")
        else:
            tree.insert(parent='', index='end', text=count+1, iid=count+1, values=values, tag="gray")

    tree.pack()
    show.mainloop()

def click_get_image():
    location = entry_image.get()
    image = cv2.imread(location)
    cv2.imshow("image", image)


def click_update():
    parking_id = entry_parking_id.get()
    license_plate = entry_license_plate.get()
    card_id = entry_card_id.get()
    time_in = entry_time_in.get()
    time_out = entry_time_out.get()
    state = entry_state.get()
    DB_update_parking(parking_id,license_plate,card_id,time_in,time_out,state)

def click_delete():
    parking_id = entry_parking_id.get()
    DB_delete_parking(parking_id)

label_instruction = Label(root, text="- Để truy suất thông tin: sử dùng phần Parking ID, Card_ID và License_plate các ô khác không ảnh hưởng.\n\
Để tra cứu với Parking ID ta dùng cú pháp \"<năm,tháng,ngày>%\" \n\
    Ví dụ muốn truy suất lịch sử ra vào của ngày 25/08/2023 thì cú pháp là \"230825%\" \n\
    Ví dụ muốn truy suất lịch sử ra vào của tháng 8 năm 2023 thì cú pháp là \"2308%\" \n\
    Ví dụ muốn truy suất lịch sử ra vào của năm 2023 thì cú pháp là \"23%\" \n\
Để tra cứu với Card_ID ta dùng cú pháp \"<Mã thẻ>\" \n\
Để tra cứu với License_plate ta dùng cú pháp \"<Ký tự hàng 1 viết liền> + <Shift gạch \"_\"> + <ký tự hàng 2 viết liền>\" \n\
Để tra cứu với Parking ID và Card_ID ta điền 2 ô này theo cú pháp phía trên\
Nhấn Search\n\
- Để cập nhật thông tin:\n\
Điền Parking ID để chọn dòng lịch sử muốn chỉnh sửa\n\
Điền các thông tin muốn cập nhật vào các ô còn lại trừ Image. Với ô không chỉnh sửa để trống\n\
Nhấn Update\n\
- Để lưu thông tin:\n\
Điền các thông tin muốn cập nhật vào các ô còn lại trừ Parking ID, Image. Với ô không chỉnh sửa để trống\n\
Điền Parking ID là \"_\" \n\
Nhất Update\n\
- Để xóa thông tin:\n\
Điền Parking ID muốn xóa, các ô khác không ảnh hưởng \n\
Nhất Delete\n\
- Để xem hình từ database:\n\
Điền dữ liệu ở cột IMAGEIN hoặc IMAGEOUT sau khi truy suất vào ô Image \n\
Nhấn Enter\n\
- Để điền ô TIMEIN và TIMEOUT theo format \"YYYY/MM/DD-hh:mm:ss\""

                                    , font="courier 10 normal", justify=LEFT)

label_parking_id = Label(root, text="Parking ID:"
                                    , font="courier 14 normal")

label_license_plate = Label(root, text="Lisence Plate:"
                                    , font="courier 14 normal")

label_card_id = Label(root, text="Card ID:"
                                    , font="courier 14 normal")

label_time_in = Label(root, text="Time In:"
                                    , font="courier 14 normal")

label_time_out = Label(root, text="Time Out:"
                                    , font="courier 14 normal")

label_state = Label(root, text="State:"
                                    , font="courier 14 normal")

label_image = Label(root, text="Image URL:"
                                    , font="courier 14 normal")

entry_parking_id = Entry(root, bg="white", fg="black"
                            , font="courier 15 normal", bd=3, width=10)

entry_license_plate = Entry(root, bg="white", fg="black"
                            , font="courier 15 normal", bd=3, width=10)

entry_card_id = Entry(root, bg="white", fg="black"
                            , font="courier 15 normal", bd=3, width=10)

entry_time_in = Entry(root, bg="white", fg="black"
                            , font="courier 15 normal", bd=3, width=10)

entry_time_out = Entry(root, bg="white", fg="black"
                            , font="courier 15 normal", bd=3, width=10)

entry_state = Entry(root, bg="white", fg="black"
                            , font="courier 15 normal", bd=3, width=10)

entry_image= Entry(root, bg="white", fg="black"
                            , font="courier 15 normal", bd=3, width=10)

button_search = Button(root, text="Search", font="courier 14 normal", command=click_search)

button_update = Button(root, text="Update", font="courier 14 normal", command=click_update)

button_delete = Button(root, text="Delete", font="courier 14 normal", command=click_delete)

button_get_image = Button(root, text="Enter", font="courier 14 normal", command=click_get_image)


label_parking_id.grid(row=0, column=0, sticky=W)
entry_parking_id.grid(row=0, column=1)
button_search.grid(row=0, column=2)
button_update.grid(row=0, column=3)
button_delete.grid(row=0, column=4)

label_license_plate.grid(row=1, column=0, sticky=W)
entry_license_plate.grid(row=1, column=1)

label_card_id.grid(row=2, column=0, sticky=W)
entry_card_id.grid(row=2, column=1)

label_time_in.grid(row=3, column=0, sticky=W)
entry_time_in.grid(row=3, column=1)

label_time_out.grid(row=4, column=0, sticky=W)
entry_time_out.grid(row=4, column=1)

label_state.grid(row=5, column=0, sticky=W)
entry_state.grid(row=5, column=1)

label_image.grid(row=6, column=0, sticky=W)
entry_image.grid(row=6,column=1)

button_get_image.grid(row=6,column=2)


label_instruction.grid(columnspan=50,sticky=W)
root.mainloop()