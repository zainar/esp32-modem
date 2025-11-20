#ifndef USB_CDC_ECM_H
#define USB_CDC_ECM_H

#include "esp_err.h"
#include <stdint.h>
#include <stdbool.h>

/**
 * @brief Initialize USB CDC-ECM interface
 * 
 * @return esp_err_t ESP_OK on success
 */
esp_err_t usb_cdc_ecm_init(void);

/**
 * @brief Send data over USB CDC-ECM
 * 
 * @param data Data to send
 * @param len Length of data
 * @return esp_err_t ESP_OK on success
 */
esp_err_t usb_cdc_ecm_send(const uint8_t *data, uint16_t len);

/**
 * @brief Register callback for received data
 * 
 * @param callback Function to call when data is received
 * @return esp_err_t ESP_OK on success
 */
esp_err_t usb_cdc_ecm_register_rx_callback(void (*callback)(const uint8_t *data, uint16_t len));

/**
 * @brief Check if USB CDC-ECM is ready
 * 
 * @return true if ready
 */
bool usb_cdc_ecm_is_ready(void);

#endif // USB_CDC_ECM_H

