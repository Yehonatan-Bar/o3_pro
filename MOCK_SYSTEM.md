# Mock System Documentation

The mock system allows you to capture API responses and replay them for testing without making actual API calls.

## How it works

1. **Capture Mode (Default)**: All API calls are made normally and responses are logged
2. **Mock Mode**: Previously captured responses are used instead of making API calls

## Files Created

- `logs/all_prompt_responses.jsonl` - Persistent log of all prompt/response pairs (JSONL format)
- `mock_data/captured_responses.json` - Formatted mock data for testing (JSON format)

## Step-by-Step Usage

### Step 1: Capture Real Responses

1. Ensure mock mode is OFF (default):
   ```bash
   # Mock mode is off by default, but you can verify:
   unset MOCK_MODE  # or export MOCK_MODE=false
   ```

2. Run your analysis normally:
   ```bash
   python app.py
   ```

3. Upload files and run analysis through the web interface
4. All API calls will be captured automatically

### Step 2: Export Mock Data

After capturing responses, export them to mock format:

```bash
curl http://localhost:9000/api/export-mock-data
```

Or use the test script:
```bash
python test_mock_system.py
```

### Step 3: Enable Mock Mode

Set the environment variable and restart:

```bash
export MOCK_MODE=true
python app.py
```

### Step 4: Test with Mocks

Now when you run analyses, the system will use captured responses instead of making API calls.

## API Endpoints

### `GET /api/mock-status`
Returns current mock system status:
- Mock mode enabled/disabled
- File locations and existence
- Number of available mock responses

### `GET /api/export-mock-data`
Exports captured responses to mock data file:
- Reads from persistent logs
- Combines with current session
- Saves to mock data file

### `GET /api/prompt-logs`
View captured prompt/response pairs (enhanced with file info):
- All standard filtering options
- Additional metadata for mocking

## Enhanced Logging

The logging system now captures:
- **prompt_hash**: Short hash for matching requests
- **model_used**: Which model was used (o3, o3-pro, or mock)
- **file_names**: Names/IDs of uploaded files
- **file_hashes**: Hashes of uploaded files
- **timestamp**: When the request was made

## Response Matching

Mock responses are matched by:
1. **Exact prompt hash**: Fast hash-based lookup
2. **Exact prompt text**: Fallback for robustness

## Benefits

1. **Faster Testing**: No API calls needed
2. **Consistent Results**: Same responses every time
3. **Cost Savings**: No API usage during testing
4. **Offline Testing**: Works without internet connection
5. **Debugging**: Reproduce exact scenarios

## Example Usage

```bash
# 1. Capture responses (normal mode)
python app.py
# Upload files, run analysis

# 2. Export to mock format
curl http://localhost:9000/api/export-mock-data

# 3. Enable mock mode
export MOCK_MODE=true
python app.py

# 4. Test with mocks
# Upload same files - will use captured responses
```

## Troubleshooting

- **No mock responses found**: Ensure you've run `/api/export-mock-data` after capturing
- **Mock mode not working**: Check `MOCK_MODE=true` environment variable
- **File not found errors**: Check that `logs/` and `mock_data/` directories exist
- **Hash mismatches**: Try running with same files and guideline sets used during capture