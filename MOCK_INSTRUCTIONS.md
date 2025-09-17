# 🎭 Mock System Instructions

## Quick Start

### 1. Enable Mock Mode
```bash
./toggle_mock.sh on
```

### 2. Start App
```bash
python app.py
```

### 3. Test
Upload files and run analysis - it will use cached responses instead of API calls!

## Commands

```bash
./toggle_mock.sh on      # Enable mock mode
./toggle_mock.sh off     # Enable live mode
./toggle_mock.sh status  # Check current mode
```

## How It Works

- **Live Mode (Default)**: Makes real API calls to OpenAI
- **Mock Mode**: Uses pre-captured responses from `mock_responses.json`

## Mock Responses Available

✅ **גובה מזקף ראש מעל מדרגות** - Result: -1 (Unknown)
✅ **שיפוע השלח** - Result: -1 (Unknown)
✅ **סטיה מותרת באחידות מידות המדרגות** - Result: -1 (Unknown)
✅ **מעקה, מסעד ובית אחיזה** - Result: -1 (Unknown)
✅ **אף המדרגה וזווית הרום** - Result: -1 (Unknown)

## Benefits

- ⚡ **Instant Results** - No API delays
- 💰 **No API Costs** - Uses cached responses
- 🔄 **Consistent Testing** - Same results every time
- 📶 **Offline Testing** - Works without internet

## Adding More Mock Responses

Edit `mock_responses.json` and add:
```json
{
  "Your Guideline Title": {
    "result": 1,  // 1=כן, 0=לא, -1=Unknown
    "explanation": "Your explanation text here..."
  }
}
```

## Troubleshooting

- **Mock not working**: Check `./toggle_mock.sh status` and restart app
- **Missing responses**: Add them to `mock_responses.json`
- **API still called**: Ensure `MOCK_MODE=true` environment variable is set