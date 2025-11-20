#ifndef WIFI_BRIDGE_H
#define WIFI_BRIDGE_H

#include "esp_err.h"

/**
 * @brief Initialize WiFi bridge module
 * 
 * @return esp_err_t ESP_OK on success
 */
esp_err_t wifi_bridge_init(void);

/**
 * @brief Connect to WiFi network
 * 
 * @param ssid WiFi SSID
 * @param password WiFi password
 * @return esp_err_t ESP_OK on success
 */
esp_err_t wifi_bridge_connect(const char *ssid, const char *password);

/**
 * @brief Disconnect from WiFi
 * 
 * @return esp_err_t ESP_OK on success
 */
esp_err_t wifi_bridge_disconnect(void);

/**
 * @brief Get WiFi connection status
 * 
 * @return true if connected
 */
bool wifi_bridge_is_connected(void);

/**
 * @brief Send packet from USB to WiFi
 * 
 * @param data Packet data
 * @param len Packet length
 * @return esp_err_t ESP_OK on success
 */
esp_err_t wifi_bridge_send_to_wifi(const uint8_t *data, uint16_t len);

/**
 * @brief Send packet from WiFi to USB
 * 
 * @param data Packet data
 * @param len Packet length
 * @return esp_err_t ESP_OK on success
 */
esp_err_t wifi_bridge_send_to_usb(const uint8_t *data, uint16_t len);

#endif // WIFI_BRIDGE_H

