#!/bin/bash

# Script to toggle between mock and live mode

case "$1" in
    "on"|"mock"|"enable")
        echo "🎭 Enabling MOCK MODE..."
        echo "export MOCK_MODE=true" > .env_mock
        echo "✅ Mock mode enabled. Now run:"
        echo "   source .env_mock && python app.py"
        echo "   OR"
        echo "   MOCK_MODE=true python app.py"
        ;;
    "off"|"live"|"disable")
        echo "🌐 Enabling LIVE MODE..."
        echo "export MOCK_MODE=false" > .env_mock
        echo "✅ Live mode enabled. Now run:"
        echo "   source .env_mock && python app.py"
        echo "   OR"
        echo "   MOCK_MODE=false python app.py"
        ;;
    "status")
        if [ -f ".env_mock" ]; then
            source .env_mock
        fi
        if [ "$MOCK_MODE" = "true" ]; then
            echo "🎭 Current mode: MOCK (using cached responses)"
        else
            echo "🌐 Current mode: LIVE (making real API calls)"
        fi
        ;;
    "run")
        echo "🚀 Starting app with current settings..."
        if [ -f ".env_mock" ]; then
            source .env_mock
            python app.py
        else
            echo "No settings found, starting in LIVE mode..."
            python app.py
        fi
        ;;
    *)
        echo "Usage: $0 {on|off|status|run}"
        echo ""
        echo "Commands:"
        echo "  on/mock/enable  - Enable mock mode (use cached responses)"
        echo "  off/live/disable - Enable live mode (make real API calls)"
        echo "  status          - Show current mode"
        echo "  run             - Start app with current settings"
        echo ""
        echo "Examples:"
        echo "  $0 on && $0 run     # Enable mock mode and start"
        echo "  $0 off && $0 run    # Enable live mode and start"
        echo "  $0 status           # Check current mode"
        echo ""
        echo "Alternative (manual):"
        echo "  MOCK_MODE=true python app.py   # Start in mock mode"
        echo "  MOCK_MODE=false python app.py  # Start in live mode"
        exit 1
        ;;
esac