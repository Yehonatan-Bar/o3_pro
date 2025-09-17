# o3-pro Multi-PDF Analyzer & Compliance Checker

A comprehensive Flask-based web application that enables analysis of multiple PDF documents using OpenAI's o3-pro model. The application supports both traditional document analysis and advanced guideline-based compliance checking for regulatory and policy verification.

## 🚀 **Latest Updates (Feb 2025)**

### **Infrastructure-Proof Architecture**
- **Persistent Job Storage** - All jobs survive server restarts and proxy timeouts
- **Heartbeat System** - Keeps long-running o3-pro calls alive during 12+ minute processing
- **Recovery Mechanism** - Resume interrupted jobs with "🔄 Recover Job" button
- **GitHub Codespaces Compatible** - Handles 60-second proxy timeout limits
- **Real-time Status Tracking** - Individual guideline progress with live updates

### **Enhanced Reliability**
- **Comprehensive Logging** - Server and client-side debugging information
- **Error Recovery** - Graceful handling of API timeouts and connection issues
- **Parallel Processing** - Multiple guidelines analyzed simultaneously with staggered delays
- **Robust Validation** - Complete form validation and error messaging
- **JSON Error Handling** - Detailed debugging for API response issues

## Features

### 🔍 Multi-PDF Analysis
- **Upload multiple PDF files simultaneously** for combined analysis
- **Single PDF support** - maintains backward compatibility
- **Real-time file validation** - ensures only PDF files are processed
- **File preview** - shows selected files with sizes before upload

### 📋 Guidelines-Based Compliance Checking
- **Advanced JSON-Based Analysis** - Model returns structured JSON with numeric results and detailed explanations
- **Regulatory Compliance Analysis** - systematic verification against predefined guidelines
- **Multiple Guidelines Sets** - supports various compliance frameworks:
  - **Compliance Guidelines** - GDPR, data retention, security measures
  - **Technical Guidelines** - API documentation, system requirements, code quality
  - **Quality Assurance Guidelines** - review processes, quality metrics, testing
  - **Documentation Guidelines** - user manuals, installation guides, troubleshooting
  - **Israeli Stairs Building Regulations** - comprehensive building code compliance (Hebrew)
- **Structured Response Format**:
  - **Result codes**: 1 (compliant), 0 (non-compliant), -1 (cannot determine)
  - **Detailed explanations** with exact location references (page, section, BBox coordinates)
  - **Visual descriptions** of where information was found in documents
  - **Brief quotes** from source material (up to 15 words)
- **Individual Guideline Assessment** - each guideline evaluated with כן/לא/Unknown status
- **Interactive Explanations** - Click info icon (i) to reveal detailed reasoning
- **Progress Tracking** - real-time updates showing current guideline being analyzed
- **Compliance Reporting** - detailed summary with statistics and individual results

### 🌐 Enhanced Web Interface
- **Dual Analysis Modes** - choose between traditional analysis or guidelines-based compliance
- **Guidelines Set Selection** - dropdown interface for selecting compliance framework
- **Real-time progress tracking** with detailed status updates per guideline
- **Custom prompt support** - specify your own analysis instructions for traditional mode
- **Advanced Results Display**:
  - **Summary Reports** with compliance statistics and copy functionality
  - **Individual Guideline Results** with color-coded compliance status (green/red/yellow)
  - **Interactive Explanations** - Click info icon (i) next to status to view detailed reasoning
  - **Expandable Explanation Boxes** - Blue-tinted boxes showing location references and quotes
  - **Expandable Regulation Text** for reference and verification
  - **Copy-to-clipboard** functionality for both summaries and individual analyses
- **File information display** showing processed files and analysis details
- **📋 Prompt/Response Logs** - comprehensive logging interface for tracking all AI interactions:
  - **Complete conversation history** with timestamps and session tracking
  - **Advanced search and filtering** by text content, session, and guideline title
  - **Multiple sorting options** (timestamp, title, session)
  - **Session-based organization** for easy analysis tracking
  - **Detailed prompt and response viewing** with syntax highlighting

### 🔧 API Endpoints
- **REST API** for programmatic access
- **Multiple file upload support** via API
- **JSON responses** with structured analysis results
- **Guidelines-based analysis support** through API
- **Error handling** and validation

### 🖥️ Command Line Interface
- **Terminal-based script** (`test_upload.py`) for CLI analysis
- **Batch processing** - analyze multiple files from command line
- **Interactive mode** for file selection and custom prompts
- **Progress indicators** and detailed logging

## Installation

### Prerequisites
- Python 3.8+
- OpenAI API key with access to o3-pro model

### Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd o3_pro
   ```

2. Install dependencies:
   ```bash
   pip install flask openai
   ```

3. Set up environment variables:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   # or alternatively
   export OPENAI_API_KEY_2="your-openai-api-key"
   ```

## Usage

### Web Application

1. Start the Flask server:
   ```bash
   python app.py
   ```

2. Open your browser and navigate to `http://localhost:9000`

3. **Upload Files:**
   - Click "Choose Files" or drag and drop PDF files
   - Select multiple PDFs at once (Ctrl+click or Cmd+click)
   - Files are validated in real-time

4. **Select Analysis Mode:**
   - **Guidelines-Based Analysis:** Choose from predefined compliance frameworks
   - **Traditional Analysis:** Use custom prompts for general document analysis

5. **Guidelines Mode (Recommended):**
   - Select a guidelines set from the dropdown (e.g., "Israeli Stairs Regulations")
   - System will automatically analyze each guideline against your documents
   - Real-time progress shows current guideline being processed

6. **Traditional Mode:**
   - Enter specific analysis instructions in the prompt field
   - Default: "Read the attached files and give me a concise summary with three key takeaways from each file."

7. **View Results:**
   - **Guidelines Analysis:** Comprehensive compliance report with:
     - Summary statistics (compliant/non-compliant/unknown)
     - Individual guideline results with color-coded status
     - Detailed analysis text for each guideline
     - Reference regulation text (expandable)
   - **Traditional Analysis:** Standard document analysis results
   - Copy functionality for all result types

### API Usage

#### Traditional Analysis
```bash
curl -X POST http://localhost:9000/api/analyze \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf" \
  -F "files=@document3.pdf" \
  -F "prompt=Analyze these documents for compliance requirements"
```

#### Guidelines-Based Analysis
```bash
curl -X POST http://localhost:9000/api/analyze \
  -F "files=@architectural_plans.pdf" \
  -F "files=@specifications.pdf" \
  -F "guideline_set=israeli_stairs_regulations"
```

#### Response Formats

**Traditional Analysis Response:**
```json
{
  "filenames": ["document1.pdf", "document2.pdf"],
  "file_count": 2,
  "analysis": "Detailed analysis results...",
  "prompt": "Custom prompt used"
}
```

**Guidelines Analysis Response:**
```json
{
  "filenames": ["architectural_plans.pdf", "specifications.pdf"],
  "file_count": 2,
  "analysis_type": "guidelines",
  "result": {
    "guideline_set_name": "תקנות תכנון ובניה - מדרגות",
    "guideline_results": [
      {
        "guideline_id": "stairs_width_compliance",
        "title": "רוחב של מדרגות",
        "compliance_status": "כן",
        "analysis": "{\"result\": 1, \"explanation\": \"ההנחיה דורשת רוחב ≥1.10m. בקובץ 'specifications.pdf', עמוד 3, סעיף 4.2 'מדרגות', מופיע: 'רוחב נטו 1.15m'. תיאור מיקום: באמצע העמוד, טבלת מידות, שורה שלישית.\"}",
        "explanation": "ההנחיה דורשת רוחב ≥1.10m. בקובץ 'specifications.pdf', עמוד 3, סעיף 4.2 'מדרגות', מופיע: 'רוחב נטו 1.15m'. תיאור מיקום: באמצע העמוד, טבלת מידות, שורה שלישית.",
        "regulation_text": "רוחבן של מדרגות בבניין יהיה 1.10 מטרים לפחות..."
      }
    ],
    "summary": "# סיכום דוח ניתוח הנחיות\n\n## תוצאות כלליות:\n- סך הכל הנחיות שנבדקו: 10\n- עמידה בדרישות (כן): 7\n- אי עמידה בדרישות (לא): 2\n- לא ברור/אין מידע (Unknown): 1"
  }
}
```

### Command Line Interface

#### Interactive Mode
```bash
python test_upload.py
```

#### Command Line Arguments
```bash
# Single file
python test_upload.py document.pdf

# Multiple files
python test_upload.py doc1.pdf doc2.pdf doc3.pdf
```

#### Features
- File existence validation
- Progress tracking for each upload
- Custom prompt input
- Detailed analysis results

## File Structure

```
o3_pro/
├── app.py                 # Main Flask application with dual analysis modes
├── test_upload.py         # Command line interface
├── templates/
│   ├── index.html        # Main upload page with guidelines selection
│   ├── status.html       # Processing status page with recovery mechanism
│   ├── result.html       # Enhanced results display for both analysis modes
│   └── logs.html         # Prompt/response logs viewer with filtering and search
├── uploads/              # Temporary file storage (auto-cleanup)
├── jobs/                 # Persistent job storage for recovery (auto-created)
├── prompt_library.xml    # Prompt templates and system prompts (Hebrew/English)
├── guidelines_sets.xml   # Guidelines definitions and regulation text
├── app.log               # Server-side logging output
└── README.md            # This documentation
```

## Technical Details

### Backend Architecture
- **Flask framework** for web server with dual processing modes and persistent job storage
- **Asynchronous processing** using threading with heartbeat system for long-running operations
- **File upload handling** with Unicode filename support and comprehensive validation
- **OpenAI API integration** using the Responses API with extended timeout (20 minutes)
- **XML-based configuration** for guidelines and prompts with full Hebrew support
- **Automatic cleanup** of temporary files and uploaded OpenAI files
- **Persistent job storage** - JSON-based job persistence surviving server restarts
- **Recovery system** - Job recovery mechanism for interrupted processing
- **📊 Comprehensive Logging System** - In-memory prompt/response tracking with web interface:
  - **Real-time conversation capture** - All prompts and responses automatically logged
  - **Session-based organization** - Grouped by analysis job for easy tracking
  - **Advanced filtering and search** - Find specific interactions by content or metadata
  - **Memory management** - Automatic cleanup with configurable limits (1000 entries)
  - **RESTful API** - `/api/prompt-logs` endpoint with sorting and filtering capabilities

### OpenAI o3-pro Integration
- **Multiple file support** - uploads all PDFs to OpenAI file storage
- **Dual analysis modes**:
  - **Traditional Mode:** Combined analysis with custom prompts
  - **Guidelines Mode:** Parallel analysis per guideline with 10-second staggered delays
- **Reasoning effort** - set to "high" for thorough compliance analysis (12+ minutes per call)
- **Structured responses** - processes and formats model output for both modes
- **Progress tracking** - real-time status updates with individual guideline monitoring
- **Heartbeat system** - keeps jobs alive during extended API calls
- **File cleanup** - automatically deletes files from OpenAI after analysis
- **Error resilience** - handles API timeouts, retries, and connection issues

### Guidelines Processing Engine
- **XML Configuration Loading** - dynamic parsing of guidelines sets and prompt templates
- **Parallel Processing Loop** - processes multiple guidelines simultaneously with controlled concurrency
- **Prompt Construction** - combines system prompts, general analysis instructions, regulation text, and uploaded documents
- **JSON Response Processing**:
  - **Robust JSON extraction** - handles both clean JSON and embedded JSON in text
  - **Fallback mechanisms** - reverts to text-based detection if JSON parsing fails
  - **Result mapping** - converts numeric codes (1/0/-1) to Hebrew status (כן/לא/Unknown)
  - **Explanation extraction** - captures detailed reasoning with location references
- **Compliance Detection** - extracts structured responses with explanations from model output
- **Report Generation** - creates comprehensive Hebrew summary reports with statistics
- **Real-time Progress Broadcasting** - updates job status with individual guideline completion status
- **Individual Error Handling** - isolates failures to specific guidelines without stopping others
- **Status Persistence** - saves progress after each guideline completion

### Security Features
- **File type validation** - only accepts PDF files
- **Secure filename handling** - prevents directory traversal
- **Temporary file cleanup** - removes files after processing
- **Error handling** - graceful failure recovery

## Configuration

### Environment Variables
- `OPENAI_API_KEY` or `OPENAI_API_KEY_2`: Your OpenAI API key
- `UPLOAD_FOLDER`: Directory for temporary file storage (default: 'uploads')

### Configuration & Customization

#### Application Settings
- **Allowed file types**: Modify `ALLOWED_EXTENSIONS` in `app.py`
- **Analysis parameters**: Adjust o3-pro reasoning effort and timeout settings
- **UI styling**: Customize CSS in HTML templates

#### Guidelines Configuration (`guidelines_sets.xml`)
- **Guidelines Sets**: Add new compliance frameworks with unique IDs
- **Individual Guidelines**: Define specific regulations with titles and regulation text
- **Multilingual Support**: Full Hebrew and English support for guidelines
- **Extensible Structure**: Easy addition of new guidelines and compliance areas

#### Prompt Configuration (`prompt_library.xml`)
- **System Prompts**: Define analysis instructions for the AI model
- **General Analysis Templates**: Reusable prompt components
- **Connecting Words**: Hebrew text connectors for prompt construction
- **Customizable Templates**: Modify prompts without code changes

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main upload page with guidelines selection |
| `/logs` | GET | Prompt/response logs viewer with filtering and search |
| `/upload` | POST | Web form file upload (supports both analysis modes) |
| `/api/analyze` | POST | API file analysis (traditional and guidelines modes) |
| `/api/status/<job_id>` | GET | Check processing status with real-time progress details |
| `/api/recover/<job_id>` | POST | Recover interrupted jobs and resume processing |
| `/api/jobs` | GET | List all jobs (in memory and persisted) |
| `/api/prompt-logs` | GET | Retrieve prompt/response logs with filtering and sorting |
| `/result/<job_id>` | GET | View analysis results (enhanced for guidelines) |

### **New Logging API**
The `/api/prompt-logs` endpoint supports:
- **Query Parameters:**
  - `sort_by`: timestamp, guideline_title, session (default: timestamp)
  - `sort_order`: asc, desc (default: desc)
  - `session`: filter by specific session/job ID
  - `search`: text search in prompts, responses, and titles
  - `limit`: number of results (default: 100, max: 500)
- **Response Format:**
  ```json
  {
    "logs": [...],
    "total_count": 150,
    "filtered_count": 25,
    "sessions": ["job-id-1", "job-id-2"]
  }
  ```

## Error Handling & Reliability

### **Robust Error Recovery System**
- **File validation errors** - Invalid file types, empty uploads, missing guideline selection
- **Connection & Proxy Issues**:
  - **GitHub Codespaces 504 Gateway Timeout** - Automatic detection and recovery options
  - **Long-running API calls** - Heartbeat system keeps jobs alive during 12+ minute o3-pro processing
  - **Network interruptions** - Connection retry logic with progressive backoff
- **API & Processing Errors**:
  - **OpenAI API failures** - Individual guideline error isolation, authentication issues
  - **Individual guideline failures** - Continue processing other guidelines
  - **JSON parsing errors** - Detailed debugging and error reporting
- **Infrastructure Issues**:
  - **Server restarts** - Jobs automatically recovered from persistent storage
  - **Proxy timeouts** - Recovery button appears with clear user instructions
  - **Memory issues** - Jobs persisted to disk with automatic cleanup
- **User Experience**: Clear error messages, recovery suggestions, and status transparency

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]

## Support

For issues and questions:

### **Common Issues & Solutions**
- **"Unexpected end of input" error**: Clear browser cache, check server logs in `app.log`
- **504 Gateway Timeout**: Click the "🔄 Recover Job" button when it appears
- **Job appears stuck**: Jobs may take 12+ minutes per guideline - check server logs for progress
- **Connection lost**: Use the recovery mechanism - jobs continue running in background

### **Verification Steps**
- Verify your OpenAI API key has access to o3-pro model
- Ensure PDF files are not corrupted or password-protected
- Verify XML configuration files (`guidelines_sets.xml`, `prompt_library.xml`) are properly formatted
- Check server logs in `app.log` for detailed error information
- For guidelines analysis issues, verify the selected guideline set exists in `guidelines_sets.xml`

### **Performance Expectations**
- **Traditional Analysis**: 2-5 minutes for multiple PDFs
- **Guidelines Analysis**: 10-15 minutes per guideline (2-3 hours for Israeli Stairs Regulations)
- **GitHub Codespaces**: May experience proxy timeouts - use recovery feature

## Key Features Summary

### ✅ Core Capabilities
- **Dual Analysis Modes** - Traditional document analysis and guidelines-based compliance checking
- **Infrastructure-Proof Processing** - Survives server restarts, proxy timeouts, and connection issues
- **Multiple PDF Support** - Simultaneous processing of multiple documents with parallel guideline analysis
- **Real-time Progress Tracking** - Individual guideline status with heartbeat monitoring
- **Job Recovery System** - Resume interrupted processing with persistent storage
- **Comprehensive Compliance Reporting** - Hebrew summary reports with detailed statistics
- **XML-Based Configuration** - Flexible guidelines and prompt management system
- **Enhanced Web Interface** - Recovery buttons, detailed error messages, progress visualization
- **📋 Advanced Logging System** - Complete prompt/response tracking with web interface:
  - **Real-time conversation capture** with automatic session organization
  - **Advanced search and filtering** by content, session, and metadata
  - **Multiple sorting options** (timestamp, title, session) with flexible display
  - **Memory-efficient storage** with automatic cleanup and size management
- **REST API Support** - Both traditional and guidelines analysis with job management endpoints
- **Command Line Interface** - Terminal-based batch processing for automation
- **Multilingual Support** - Full Hebrew and English support for regulatory compliance
- **Production-Ready Reliability** - Handles OpenAI infrastructure issues and long processing times

### 🏗️ Specialized Use Cases
- **Building Code Compliance** - Israeli stairs regulations with detailed Hebrew analysis
- **Document Quality Assurance** - Technical documentation standards verification
- **Regulatory Compliance** - GDPR, security, and policy compliance checking
- **Technical Standards** - API documentation, system requirements, and code quality assessment