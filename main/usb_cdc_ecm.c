/*
 * USB CDC-ECM (Ethernet Control Model) Implementation
 * Presents the ESP32-C3 as a USB network interface
 */

#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_err.h"
#include "driver/usb_serial_jtag.h"

#include "usb_cdc_ecm.h"
#include "wifi_bridge.h"

static const char *TAG = "usb_cdc_ecm";

// Note: ESP-IDF doesn't have native CDC-ECM support
// This is a simplified implementation using USB Serial JTAG
// For full CDC-ECM, you may need to use a custom USB stack or
// implement it using the USB peripheral directly

static void (*rx_callback)(const uint8_t *data, uint16_t len) = NULL;
static bool s_ready = false;
static TaskHandle_t rx_task_handle = NULL;

static void usb_rx_task(void *arg)
{
    uint8_t *data = (uint8_t *)malloc(1024);
    if (data == NULL) {
        ESP_LOGE(TAG, "Failed to allocate RX buffer");
        vTaskDelete(NULL);
        return;
    }

    ESP_LOGI(TAG, "USB RX task started");
    s_ready = true;

    while (1) {
        int len = usb_serial_jtag_read_bytes(data, 1024, portMAX_DELAY);
        if (len > 0) {
            ESP_LOGD(TAG, "Received %d bytes from USB", len);
            if (rx_callback) {
                rx_callback(data, len);
            }
        }
    }
}

esp_err_t usb_cdc_ecm_init(void)
{
    // Initialize USB Serial JTAG driver
    const usb_serial_jtag_driver_config_t usb_serial_config = {
        .rx_buffer_size = 1024,
        .tx_buffer_size = 1024,
    };

    ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&usb_serial_config));
    ESP_LOGI(TAG, "USB Serial JTAG driver installed");

    // Create RX task
    xTaskCreate(usb_rx_task, "usb_rx", 4096, NULL, 5, &rx_task_handle);
    if (rx_task_handle == NULL) {
        ESP_LOGE(TAG, "Failed to create RX task");
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "USB CDC-ECM initialized (using USB Serial JTAG)");
    return ESP_OK;
}

esp_err_t usb_cdc_ecm_send(const uint8_t *data, uint16_t len)
{
    if (!s_ready) {
        return ESP_ERR_INVALID_STATE;
    }

    int written = usb_serial_jtag_write_bytes(data, len, portMAX_DELAY);
    if (written != len) {
        ESP_LOGE(TAG, "Failed to write all bytes: %d/%d", written, len);
        return ESP_FAIL;
    }

    ESP_LOGD(TAG, "Sent %d bytes to USB", len);
    return ESP_OK;
}

esp_err_t usb_cdc_ecm_register_rx_callback(void (*callback)(const uint8_t *data, uint16_t len))
{
    rx_callback = callback;
    return ESP_OK;
}

bool usb_cdc_ecm_is_ready(void)
{
    return s_ready;
}

