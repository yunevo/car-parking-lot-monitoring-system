#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"

#include "lwip/err.h"
#include "lwip/sys.h"
#include "esp_intr_alloc.h"

//Library for using mqtt
#include "mqtt_client.h"

//Library for reading rfid 
#include "rc522.h"
#include "string.h"

//Library for displaying OLED 
#include "ssd1306.h"
#include "font8x8_basic.h"

//Library that supports controlling servo
#include <time.h>
#include <math.h>
#include <driver/gpio.h>
#include <driver/ledc.h>

#include "lwip/sockets.h"
#include "lwip/dns.h"
#include "lwip/netdb.h"
uint32_t MQTT_CONNECTED = 0;   // Flag of MQTT connection's state

/*Because the wifi at a car park is unlikely to change its password occasionally
So the wifi ssid and password are hard coded*/
#define WIFI_SSID      "Pea_0010" // Wifi ssid
#define WIFI_PASS      "12345678" // Wifi password
#define MAXIMUM_RETRY  10 // max wifi connection attemp 

/*Topic name*/
/*In the case of barrier topic, 
if receive message OUT: esp32 controlling the barrỉer at the leaving direction lift the barrier
if receive message IN: esp32 controlling the barrỉer at the coming direction lift the barrier*/
#define BARRIER_TOPIC "barrier" // Topic used to receive lifting barrier command from host
#define RFID_TOPIC "snapshot" // Topic used to notify when there's car coming
#define SPACE_TOPIC "space" // Topic used to receive updating parking lots command from host

/*Logging tag*/
#define RFID_TAG "RFID"
#define WIFI_TAG "WIFI_TAG"
#define MQTT_TAG "MQTT_TAG"


/*MQTT broker*/
#define MQTT_HOST "192.168.137.32" //local MQTT host address
#define MQTT_PORT 1883
#define MQTT_USERNAME "esp_out"
#define MQTT_PASSWORD "012345678"
#define MQTT_CLIENT_ID "client_esp_out"

#if CONFIG_ESP_WIFI_AUTH_OPEN
#define ESP_WIFI_SCAN_AUTH_MODE_THRESHOLD WIFI_AUTH_OPEN
#elif CONFIG_ESP_WIFI_AUTH_WEP
#define ESP_WIFI_SCAN_AUTH_MODE_THRESHOLD WIFI_AUTH_WEP
#elif CONFIG_ESP_WIFI_AUTH_WPA_PSK
#define ESP_WIFI_SCAN_AUTH_MODE_THRESHOLD WIFI_AUTH_WPA_PSK
#elif CONFIG_ESP_WIFI_AUTH_WPA2_PSK
#define ESP_WIFI_SCAN_AUTH_MODE_THRESHOLD WIFI_AUTH_WPA2_PSK
#elif CONFIG_ESP_WIFI_AUTH_WPA_WPA2_PSK
#define ESP_WIFI_SCAN_AUTH_MODE_THRESHOLD WIFI_AUTH_WPA_WPA2_PSK
#elif CONFIG_ESP_WIFI_AUTH_WPA3_PSK
#define ESP_WIFI_SCAN_AUTH_MODE_THRESHOLD WIFI_AUTH_WPA3_PSK
#elif CONFIG_ESP_WIFI_AUTH_WPA2_WPA3_PSK
#define ESP_WIFI_SCAN_AUTH_MODE_THRESHOLD WIFI_AUTH_WPA2_WPA3_PSK
#elif CONFIG_ESP_WIFI_AUTH_WAPI_PSK
#define ESP_WIFI_SCAN_AUTH_MODE_THRESHOLD WIFI_AUTH_WAPI_PSK
#endif

/*Servo configuration*/
#define ServoMsMin 0.5
#define ServoMsMax 2.5
#define ServoMs90 ((ServoMsMax+ServoMsMin)/2.0)

/*GPIO declaration*/
#define SERVO_PIN 17 // Pin used to control servo
#define BARRIER_PIN 3 // Pin used to check if there's obsticle at the barrier 
#define MISO_PIN 21 
#define MOSI_PIN 23 
#define SCK_PIN 19 
#define	SDA_PIN 22

/*Pin connected to switch attached to the ground of each parking lot to identify if the lot is being used
 If the lot is in use, the car is sure to hold the switch and ESP32 will know that*/
 /*This is just a demo version so there are only 4 switched used*/
#define PIN_1 2 // switch for the first lot
#define PIN_2 4 // switch for the second lot
#define PIN_3 5 // switch for the third lot
#define PIN_4 18 // switch for the fourth lot


/*Variables*/


char ID[14]; // string to store rfid card ID after reading the card
char topic_data[8]; // used to store topic data received via mqtt
char topic_name[8]; // used to store topic name received via mqtt
SSD1306_t dev; // declare ssd1306 object
bool state = 1; // led state
/* FreeRTOS event group to signal when we are connected*/
static EventGroupHandle_t s_wifi_event_group;
static int s_retry_num = 0;   // variable to count number of attemps to connect the wifi


/*declare function prototype*/

/*initialize gpio pins*/
void init_gpio();

/*initialize servo*/
void init_servo();

/*initialize rfid driver*/
void init_rfid();

/*Handler for event of a car leaving*/
void RFID_OUT_handler(uint8_t*);

/*Rotate servo to 90degree position*/
void servoDeg90();

/*Rotate servo to 0degree position*/
void servoDeg0();

/*lift the barrier and if there's still any obsticle at the barrier, it remains at the 90 deg position*/
void lift_barrier();

/*initialize wifi station mode of esp32*/
void wifi_init_sta();

/*wifi event handler*/
static void event_handler();

/*initialize mqtt client */
static void mqtt_app_start();

/*mqtt event handler*/
static void mqtt_event_handler();


/* The event group allows multiple bits for each event, but we only care about two events:
 * - we are connected to the AP with an IP
 * - we failed to connect after the maximum amount of retries */
#define WIFI_CONNECTED_BIT BIT0
#define WIFI_FAIL_BIT      BIT1


///////////////////////////////////////////
// MAIN 
///////////////////////////////////////////

void app_main(void) {
	//Initialize NVS
	esp_err_t ret = nvs_flash_init();
	if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
		ESP_ERROR_CHECK(nvs_flash_erase());
		ret = nvs_flash_init();
	}
	ESP_ERROR_CHECK(ret);

	// start wifi station mode
	wifi_init_sta();

	// connect MQTT 
	mqtt_app_start();

	// Initialize barrier state pin and pwm and position servo to 0 deg
	init_gpio();
	init_servo();
	servoDeg0(SERVO_PIN);
	
	// Initialize rfid driver
	init_rfid();
}



///////////////////////////////////////////
// FUNCTIONS FOR WIFI 
///////////////////////////////////////////


/*wifi event handler*/
static void event_handler(void *arg, esp_event_base_t event_base, int32_t event_id, void *event_data) {
	// after start wifi station successfully, connect to the wifi to communicate with other devices via mqtt
	if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
		esp_wifi_connect();
		ESP_LOGI(WIFI_TAG, "Trying to connect with Wi-Fi\n");
	} 
	// retry to connect wifi after being disconnected until the attemps reach the Maximun value
	else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
		if (s_retry_num < MAXIMUM_RETRY) {
			esp_wifi_connect();
			s_retry_num++;
			ESP_LOGI(WIFI_TAG, "retry to connect to the AP");
		}
		else {
			xEventGroupSetBits(s_wifi_event_group, WIFI_FAIL_BIT);
			ESP_LOGI(WIFI_TAG, "connect to the AP fail");
		}
	// inform IP address after connect the wifi successfully and reret retry counting variable
	} else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
		ip_event_got_ip_t *event = (ip_event_got_ip_t*) event_data;
		ESP_LOGI(WIFI_TAG, "got ip:" IPSTR, IP2STR(&event->ip_info.ip));
		s_retry_num = 0;
		xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
	}
}


/*initialize station wifi driver */
void wifi_init_sta(void) {
	s_wifi_event_group = xEventGroupCreate();

	//  create an LwIP core task and initialize LwIP-related work.
	ESP_ERROR_CHECK(esp_netif_init());

	// create a system Event task and initialize an application event's callback function
	ESP_ERROR_CHECK(esp_event_loop_create_default());

	// create default network interface instance binding station with TCP/IP stack.
	esp_netif_create_default_wifi_sta();

	// create wifi driver task and initialize the driver with the default configuration
	wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
	ESP_ERROR_CHECK(esp_wifi_init(&cfg));

	// register event handlers for events
	esp_event_handler_instance_t instance_any_id;
	esp_event_handler_instance_t instance_got_ip;
	ESP_ERROR_CHECK(
			esp_event_handler_instance_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &event_handler, NULL, &instance_any_id));
	ESP_ERROR_CHECK(
			esp_event_handler_instance_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &event_handler, NULL, &instance_got_ip));

	// configure wifi mode as station
	wifi_config_t wifi_config = { 
		.sta = { 
			.ssid = WIFI_SSID,
			.password = WIFI_PASS,
			.threshold.authmode = ESP_WIFI_SCAN_AUTH_MODE_THRESHOLD,
			.sae_pwe_h2e = WPA3_SAE_PWE_BOTH, 
		}, 
	};
	ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
	ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
	ESP_ERROR_CHECK(esp_wifi_start());

	ESP_LOGI(WIFI_TAG, "wifi_init_sta finished.");

	// wait for event handler to set connected/fail bit to continue to inform user
	// about connecting's result
	EventBits_t bits = xEventGroupWaitBits(s_wifi_event_group,
	WIFI_CONNECTED_BIT | WIFI_FAIL_BIT,
	pdFALSE,
	pdFALSE,
	portMAX_DELAY);

	// if connected bit is set, inform user
	if (bits & WIFI_CONNECTED_BIT) {
		ESP_LOGI(WIFI_TAG, "connected to ap SSID:%s password:%s", WIFI_SSID, WIFI_PASS);
	// else if fail bit is set (after trying to reconnect 10 times), inform user
	} else if (bits & WIFI_FAIL_BIT) {
		ESP_LOGI(WIFI_TAG, "Failed to connect to SSID:%s, password:%s", WIFI_SSID, WIFI_PASS);
	// unknown event
	} else {
		ESP_LOGE(WIFI_TAG, "UNEXPECTED EVENT");
	}

	/* The event will not be processed after unregister */
	ESP_ERROR_CHECK(esp_event_handler_instance_unregister(IP_EVENT, IP_EVENT_STA_GOT_IP, instance_got_ip));
	ESP_ERROR_CHECK(esp_event_handler_instance_unregister(WIFI_EVENT, ESP_EVENT_ANY_ID, instance_any_id));
	vEventGroupDelete(s_wifi_event_group);
}


///////////////////////////////////////////
// FUNCTIONS FOR MQTT
///////////////////////////////////////////


// mqtt event handler
static void mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data) {
	ESP_LOGD(MQTT_TAG, "Event dispatched from event loop base=%s, event_id=%d", base, event_id);
	esp_mqtt_event_handle_t event = event_data;
	esp_mqtt_client_handle_t client = event->client;
	int msg_id;
	switch ((esp_mqtt_event_id_t) event_id) {

	// MQTT connected event
	case MQTT_EVENT_CONNECTED:
		// set connected flag
		MQTT_CONNECTED = 1;
		ESP_LOGI(MQTT_TAG, "MQTT_EVENT_CONNECTED");
		
		// subcribe to topic providing notification to lifting barrier
		msg_id = esp_mqtt_client_subscribe(client, BARRIER_TOPIC, 0);

		break;

	// MQTT disconnected event
	case MQTT_EVENT_DISCONNECTED:
		// set unconnected flag
		MQTT_CONNECTED = 0;
		ESP_LOGI(MQTT_TAG, "MQTT_EVENT_DISCONNECTED");

		break;

	// MQTT successfully subcribed event
	case MQTT_EVENT_SUBSCRIBED:
		// print out subcribed topic
		ESP_LOGI(MQTT_TAG, "MQTT_EVENT_SUBSCRIBED, msg_id=%d", event->msg_id);
		printf("TOPIC = %.*s\r\n", event->topic_len, event->topic);

		break;

	// MQTT unsubcribed event
	case MQTT_EVENT_UNSUBSCRIBED:
		ESP_LOGI(MQTT_TAG, "MQTT_EVENT_UNSUBSCRIBED, msg_id=%d", event->msg_id);
		break;

	// MQTT successfully published event
	case MQTT_EVENT_PUBLISHED:
		ESP_LOGI(MQTT_TAG, "MQTT_EVENT_PUBLISHED, msg_id=%d", event->msg_id);
		break;

	// MQTT data received event
	case MQTT_EVENT_DATA:
		// get topic name
		sprintf(topic_data, "%.*s", event->data_len, event->data);
		// get message content
		sprintf(topic_name, "%.*s", event->topic_len, event->topic);

		// if the message is intended for coming-direction ESP to lift barrier
		if (!strcmp(topic_data, "OUT")) {
			// lift barrier
			lift_barrier();
		}

		break;

	case MQTT_EVENT_ERROR:
		ESP_LOGI(MQTT_TAG, "MQTT_EVENT_ERROR");
		break;
	default:
		ESP_LOGI(MQTT_TAG, "Other event id:%d", event->event_id);
		break;
	}
}

esp_mqtt_client_handle_t client = NULL;


static void mqtt_app_start(void) {

	// MQTT configuration
	ESP_LOGI(MQTT_TAG, "STARTING MQTT");
	esp_mqtt_client_config_t mqttConfig = { 
		.host = MQTT_HOST, 
		.port = MQTT_PORT, 
		.username = MQTT_USERNAME, 
		.password = MQTT_PASSWORD, 
		.client_id = MQTT_CLIENT_ID, 
	};

	// MQTT initialization
	client = esp_mqtt_client_init(&mqttConfig);

	// register event handler
	esp_mqtt_client_register_event(client, ESP_EVENT_ANY_ID, mqtt_event_handler, client);

	// MQTT client starts and connects to MQTT broker
	esp_mqtt_client_start(client);
}

///////////////////////////////////////////
// FUNCTIONS FOR RFID
///////////////////////////////////////////

void init_rfid() {
	// pin configuration
	const rc522_start_args_t RFID_OUT = { 
		.miso_io = MISO_PIN, 
		.mosi_io = MOSI_PIN, 
		.sck_io = SCK_PIN, 
		.sda_io = SDA_PIN, 
		.callback = &RFID_OUT_handler,
		.spi_host_id = HSPI_HOST 
	};
	// start rfid driver
	rc522_start(RFID_OUT);
}

/*Read ID from RFID card and append the O letter to specify that a car is leaving
with the RFID card storing that ID*/
void RFID_OUT_handler(uint8_t *sn) {

	sprintf(ID, "O%X%X%X%X%X", sn[0], sn[1], sn[2], sn[3], sn[4]);
	ESP_LOGI(RFID_TAG, "%s", ID);
	//Publish ID read from RFID card via RFID_TOPIC
	if (MQTT_CONNECTED) {
		esp_mqtt_client_publish(client, RFID_TOPIC, ID, 0, 0, 0);
	}
}

///////////////////////////////////////////
// FUNCTIONS FOR BARRIER HANDLING (SERVO)
///////////////////////////////////////////
void init_gpio() {
	gpio_pad_select_gpio(BARRIER_PIN);
	gpio_set_direction(BARRIER_PIN, GPIO_MODE_INPUT);
}

void lift_barrier() {

	// rotate servo to 90deg position
	servoDeg90(SERVO_PIN);

	// wait for car to pass
	vTaskDelay(2000 / portTICK_PERIOD_MS);

	// check if there's still obsticle at the barrier and continue to wait
	// until the obsticle moves to exit the loop
	while (!gpio_get_level(BARRIER_PIN)) {
		vTaskDelay(2000 / portTICK_PERIOD_MS);
	}

	// rotate servo back to 0 deg position after the obsticle moves a away
	if (gpio_get_level(BARRIER_PIN))
		servoDeg0(SERVO_PIN);
}

/*set configuration for PWM*/
void init_servo() {
	// configure timer
	ledc_timer_config_t ledc_timer = { 
		.speed_mode = LEDC_LOW_SPEED_MODE,
		.timer_num = LEDC_TIMER_0, 
		.duty_resolution = LEDC_TIMER_13_BIT,
		.freq_hz = 50, 
		.clk_cfg = LEDC_AUTO_CLK 
	};
	ledc_timer_config(&ledc_timer);

	// configure channel
	ledc_channel_config_t ledc_channel = { 
		.speed_mode = LEDC_LOW_SPEED_MODE,
		.channel = LEDC_CHANNEL_0, 
		.timer_sel = LEDC_TIMER_0, 
		.intr_type =LEDC_INTR_DISABLE, 
		.gpio_num = SERVO_PIN, 
		.duty = 0,
		.hpoint = 0 
	};
	ledc_channel_config(&ledc_channel);
}

/*Move barrier to 0 deg position*/
void servoDeg0() {
	int duty = (int) (100.0 * (ServoMsMin / 20.0) * 81.91);
	ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, duty);
	ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
}

/*Move barrier to 90 deg position*/
void servoDeg90() {
	int duty = (int) (100.0 * (ServoMs90 / 20.0) * 81.91);
	ledc_set_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0, duty);
	ledc_update_duty(LEDC_LOW_SPEED_MODE, LEDC_CHANNEL_0);
}



