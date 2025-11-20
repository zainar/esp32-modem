#!/bin/bash
# check_cdc_ecm.sh - Quick check for CDC-ECM support in ESP-IDF

IDF_PATH=${IDF_PATH:-$HOME/esp/esp-idf}

echo "Checking for CDC-ECM support in ESP-IDF..."
echo "ESP-IDF path: $IDF_PATH"
echo ""

if [ ! -d "$IDF_PATH" ]; then
    echo "Error: ESP-IDF not found at $IDF_PATH"
    echo "Set IDF_PATH environment variable or install ESP-IDF"
    exit 1
fi

# Check in source
echo "1. Searching source code for CDC-ECM..."
MATCHES=$(grep -r "CDC_ECM\|cdc_ecm" "$IDF_PATH/components" 2>/dev/null | wc -l)
if [ "$MATCHES" -gt 0 ]; then
    echo "   ✓ Found $MATCHES CDC-ECM references"
    grep -r "CDC_ECM\|cdc_ecm" "$IDF_PATH/components" 2>/dev/null | head -3
else
    echo "   ✗ No CDC-ECM found in source"
fi

# Check for headers
echo ""
echo "2. Searching for CDC-ECM headers..."
HEADERS=$(find "$IDF_PATH/components" -name "*cdc*ecm*.h" 2>/dev/null | wc -l)
if [ "$HEADERS" -gt 0 ]; then
    echo "   ✓ Found CDC-ECM headers:"
    find "$IDF_PATH/components" -name "*cdc*ecm*.h" 2>/dev/null
else
    echo "   ✗ No CDC-ECM headers found"
fi

# Check examples
echo ""
echo "3. Checking for CDC-ECM examples..."
EXAMPLES=$(find "$IDF_PATH/examples" -path "*usb*" \( -name "*cdc*" -o -name "*ecm*" \) 2>/dev/null | wc -l)
if [ "$EXAMPLES" -gt 0 ]; then
    echo "   ✓ Found CDC-ECM examples:"
    find "$IDF_PATH/examples" -path "*usb*" \( -name "*cdc*" -o -name "*ecm*" \) 2>/dev/null | head -5
else
    echo "   ✗ No CDC-ECM examples found"
fi

# Check USB device components
echo ""
echo "4. Checking USB device components..."
if [ -d "$IDF_PATH/components/usb" ] || [ -d "$IDF_PATH/components/driver/usb" ]; then
    echo "   ✓ USB components found"
    ls -d "$IDF_PATH/components"/*usb* 2>/dev/null | head -5
else
    echo "   ✗ No USB device components found"
fi

# Check version
echo ""
echo "5. ESP-IDF version:"
cd "$IDF_PATH" 2>/dev/null && git describe --tags 2>/dev/null || echo "   (Could not determine version)"

echo ""
echo "Check complete!"
echo ""
echo "If CDC-ECM support is found, you can update your project to use it."
echo "See CHECK_CDC_ECM_SUPPORT.md for more details."

