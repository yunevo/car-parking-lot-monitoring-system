# Project overview

This project consists of 3 ESP32 runs on ESP-IDF framework handling RFID cards, in-out barriers, and tracking available slots in the parking lot
and a server checking car enter and departure and managing data.

![task_diagram drawio](https://github.com/yunevo/car-parking-lot-monitoring-system/assets/156734673/be6f0255-86ab-46cc-b34c-dd8f755bbc4b)

Laptop's tasks:
* Read from and write into database
* MQTT communication: send messages for ESPs to lift barrier, receive RFID card ID and car in and out direction.
* Image processing and checking if the license template is matched when leaving
* Provide user's interface

ESP0's tasks:
* Read card ID stored in RFID card
* MQTT communication: send messages when car entering the parking lot, receive lifting barrier notification, receive parking slots tracking information
* Lifting entering-side barrier
* Display parking available slots onto OLED

ESP1's tasks:
* Read card ID stored in RFID card
* MQTT communication: send messages when car leaving the parking lot, receive lifting barrier notification
* Lifting leaving-side barrier

ESP2's tasks:
* Get limit switches state installed at on each parking slots surface
* MQTT communication: send parking slots tracking information
  
## Protocols and Technical points
* RTOS(FreeRTOS)
* SPI
* I2C
* MQTT


# Project component
![module](https://github.com/yunevo/car-parking-lot-monitoring-system/assets/156734673/ba5012b4-fdc9-4edb-aa89-aea9cad3bf78)

* 3 ESP32 doit devkit v1
* Laptop
* OLED
* IC 74H595
* RFID NFC 13.56MHz Module
* OLED I2C 0.96 inch
* 2 servo



