/*
 * WiFi Bridge Module
 * Handles WiFi connection and packet bridging
 */

#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "freertos/queue.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_netif.h"
#include "lwip/err.h"
#include "lwip/sys.h"
#include "lwip/sockets.h"
#include "lwip/netdb.h"
#include "lwip/ip4_addr.h"

#include "wifi_bridge.h"
#include "usb_cdc_ecm.h"
#include "wifi_config.h"

static const char *TAG = "wifi_bridge";

static EventGroupHandle_t s_wifi_event_group;
static int s_retry_num = 0;
static bool s_wifi_connected = false;
static esp_netif_t *s_netif_sta = NULL;
static int s_raw_socket = -1;
static TaskHandle_t s_wifi_rx_task = NULL;
static QueueHandle_t s_tx_queue = NULL;

#define TX_QUEUE_SIZE 10
#define MAX_PACKET_SIZE 1500

typedef struct {
    uint8_t data[MAX_PACKET_SIZE];
    uint16_t len;
} packet_t;

/* Forward declarations */
static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                              int32_t event_id, void* event_data);
static void ip_event_handler(void* arg, esp_event_base_t event_base,
                            int32_t event_id, void* event_data);
static void wifi_rx_task(void *arg);
static void wifi_tx_task(void *arg);

esp_err_t wifi_bridge_init(void)
{
    s_wifi_event_group = xEventGroupCreate();
    if (s_wifi_event_group == NULL) {
        ESP_LOGE(TAG, "Failed to create event group");
        return ESP_FAIL;
    }

    // Create default WiFi station netif
    s_netif_sta = esp_netif_create_default_wifi_sta();
    if (s_netif_sta == NULL) {
        ESP_LOGE(TAG, "Failed to create netif");
        return ESP_FAIL;
    }

    // Initialize WiFi with default configuration
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    // Register event handlers
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
                                                        ESP_EVENT_ANY_ID,
                                                        &wifi_event_handler,
                                                        NULL,
                                                        NULL));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT,
                                                        IP_EVENT_STA_GOT_IP,
                                                        &ip_event_handler,
                                                        NULL,
                                                        NULL));

    // Set WiFi mode to station
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_start());

    // Create TX queue for packets to send
    s_tx_queue = xQueueCreate(TX_QUEUE_SIZE, sizeof(packet_t));
    if (s_tx_queue == NULL) {
        ESP_LOGE(TAG, "Failed to create TX queue");
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "WiFi bridge initialized");
    return ESP_OK;
}

esp_err_t wifi_bridge_connect(const char *ssid, const char *password)
{
    if (ssid == NULL) {
        ESP_LOGE(TAG, "SSID cannot be NULL");
        return ESP_ERR_INVALID_ARG;
    }

    wifi_config_t wifi_config = {0};
    strncpy((char *)wifi_config.sta.ssid, ssid, sizeof(wifi_config.sta.ssid) - 1);
    if (password) {
        strncpy((char *)wifi_config.sta.password, password, sizeof(wifi_config.sta.password) - 1);
    }
    wifi_config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;
    wifi_config.sta.pmf_cfg.capable = true;
    wifi_config.sta.pmf_cfg.required = false;

    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_connect());

    ESP_LOGI(TAG, "WiFi connection initiated");
    return ESP_OK;
}

esp_err_t wifi_bridge_disconnect(void)
{
    ESP_ERROR_CHECK(esp_wifi_disconnect());
    s_wifi_connected = false;
    return ESP_OK;
}

bool wifi_bridge_is_connected(void)
{
    return s_wifi_connected;
}

esp_err_t wifi_bridge_send_to_wifi(const uint8_t *data, uint16_t len)
{
    if (!s_wifi_connected) {
        ESP_LOGD(TAG, "WiFi not connected, dropping packet");
        return ESP_ERR_WIFI_NOT_CONNECT;
    }

    if (len > MAX_PACKET_SIZE) {
        ESP_LOGE(TAG, "Packet too large: %d", len);
        return ESP_ERR_INVALID_SIZE;
    }

    // Queue packet for transmission
    packet_t packet;
    memcpy(packet.data, data, len);
    packet.len = len;

    if (xQueueSend(s_tx_queue, &packet, pdMS_TO_TICKS(100)) != pdTRUE) {
        ESP_LOGW(TAG, "TX queue full, dropping packet");
        return ESP_ERR_NO_MEM;
    }

    ESP_LOGD(TAG, "Queued %d bytes for WiFi transmission", len);
    return ESP_OK;
}

esp_err_t wifi_bridge_send_to_usb(const uint8_t *data, uint16_t len)
{
    return usb_cdc_ecm_send(data, len);
}

static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                              int32_t event_id, void* event_data)
{
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        ESP_LOGI(TAG, "WiFi station started");
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        if (s_retry_num < WIFI_MAX_RETRY) {
            esp_wifi_connect();
            s_retry_num++;
            ESP_LOGI(TAG, "Retry to connect to the AP");
        } else {
            xEventGroupSetBits(s_wifi_event_group, WIFI_FAIL_BIT);
            ESP_LOGE(TAG, "Connect to the AP failed");
        }
        s_wifi_connected = false;
        ESP_LOGI(TAG, "WiFi disconnected");
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_CONNECTED) {
        ESP_LOGI(TAG, "WiFi connected to AP");
        s_retry_num = 0;
    }
}

static void ip_event_handler(void* arg, esp_event_base_t event_base,
                            int32_t event_id, void* event_data)
{
    if (event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "Got IP:" IPSTR, IP2STR(&event->ip_info.ip));
        s_retry_num = 0;
        xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
        s_wifi_connected = true;

        // Create raw socket for packet reception
        // Note: Raw sockets in lwip have limitations compared to Linux
        // For now, we'll use a simpler approach with UDP/TCP sockets
        if (s_raw_socket < 0) {
            // Using UDP socket for now - raw sockets require special handling in lwip
            s_raw_socket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
            if (s_raw_socket >= 0) {
                
                // Start RX task
                if (s_wifi_rx_task == NULL) {
                    xTaskCreate(wifi_rx_task, "wifi_rx", 4096, NULL, 5, &s_wifi_rx_task);
                }
                
                // Start TX task
                xTaskCreate(wifi_tx_task, "wifi_tx", 4096, NULL, 5, NULL);
                
                ESP_LOGI(TAG, "Raw socket created for packet reception");
            } else {
                ESP_LOGE(TAG, "Failed to create raw socket");
            }
        }
    }
}

static void wifi_tx_task(void *arg)
{
    packet_t packet;
    ESP_LOGI(TAG, "WiFi TX task started");
    ESP_LOGW(TAG, "Note: Raw packet transmission not fully implemented");
    
    while (1) {
        if (xQueueReceive(s_tx_queue, &packet, portMAX_DELAY) == pdTRUE) {
            if (s_wifi_connected) {
                // For now, log the packet
                // In a full implementation, we'd parse the Ethernet frame,
                // extract the IP packet, and send it via the netif layer
                ESP_LOGD(TAG, "Received packet to send: %d bytes", packet.len);
                // TODO: Implement proper packet transmission via netif
                // This requires parsing Ethernet frames and routing IP packets
            }
        }
    }
}

static void wifi_rx_task(void *arg)
{
    uint8_t *buffer = (uint8_t *)malloc(MAX_PACKET_SIZE);
    if (buffer == NULL) {
        ESP_LOGE(TAG, "Failed to allocate RX buffer");
        vTaskDelete(NULL);
        return;
    }

    ESP_LOGI(TAG, "WiFi RX task started");
    ESP_LOGW(TAG, "Note: WiFi RX via raw sockets not fully implemented - using netif layer");

    // For now, this task is a placeholder
    // In a full implementation, we'd need to use esp_netif callbacks
    // or implement proper packet capture
    while (1) {
        vTaskDelay(pdMS_TO_TICKS(1000));
        // TODO: Implement proper packet reception from WiFi
        // This would require using esp_netif callbacks or custom netif hooks
    }
}

