idf_component_register(
    SRCS 
        "main.c"
        "wifi_bridge.c"
        "usb_cdc_ecm.c"
    INCLUDE_DIRS 
        "."
    PRIV_REQUIRES 
        esp_wifi
        esp_netif
        nvs_flash
        driver
        esp_event
        mbedtls
)

