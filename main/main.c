/*
 * ESP32-C3 WiFi USB Adapter
 * Main application entry point
 */

#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_netif.h"
#include "driver/gpio.h"

#include "wifi_bridge.h"
#include "usb_cdc_ecm.h"
#include "wifi_config.h"

static const char *TAG = "main";

// Wrapper function to bridge USB RX to WiFi
static void usb_rx_to_wifi_callback(const uint8_t *data, uint16_t len)
{
    wifi_bridge_send_to_wifi(data, len);
}

void app_main(void)
{
    ESP_LOGI(TAG, "ESP32-C3 WiFi USB Adapter starting...");

    // Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    // Initialize network interface
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());

    // Initialize WiFi bridge first (needed for packet routing)
    ESP_LOGI(TAG, "Initializing WiFi bridge...");
    if (wifi_bridge_init() != ESP_OK) {
        ESP_LOGE(TAG, "Failed to initialize WiFi bridge");
        return;
    }

    // Initialize USB CDC-ECM
    ESP_LOGI(TAG, "Initializing USB CDC-ECM...");
    if (usb_cdc_ecm_init() != ESP_OK) {
        ESP_LOGE(TAG, "Failed to initialize USB CDC-ECM");
        return;
    }

    // Register USB RX callback to bridge packets to WiFi
    usb_cdc_ecm_register_rx_callback(usb_rx_to_wifi_callback);

    // Start WiFi connection
    ESP_LOGI(TAG, "Connecting to WiFi: %s", WIFI_SSID);
    wifi_bridge_connect(WIFI_SSID, WIFI_PASSWORD);

    ESP_LOGI(TAG, "Initialization complete. Bridge is running.");
}

