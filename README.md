# o3-pro Multi-PDF Analyzer

A Flask-based web application that enables analysis of multiple PDF documents using OpenAI's o3-pro model. The application supports both single and multiple PDF file uploads for comprehensive document analysis.

## Features

### 🔍 Multi-PDF Analysis
- **Upload multiple PDF files simultaneously** for combined analysis
- **Single PDF support** - maintains backward compatibility
- **Real-time file validation** - ensures only PDF files are processed
- **File preview** - shows selected files with sizes before upload

### 🌐 Web Interface
- **Clean, responsive UI** with drag-and-drop file selection
- **Real-time progress tracking** with status updates
- **Custom prompt support** - specify your own analysis instructions
- **Results display** with copy-to-clipboard functionality
- **File information display** showing processed files and analysis details

### 🔧 API Endpoints
- **REST API** for programmatic access
- **Multiple file upload support** via API
- **JSON responses** with structured analysis results
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

4. **Custom Prompts (Optional):**
   - Enter specific analysis instructions
   - Default: "Read the attached files and give me a concise summary with three key takeaways from each file."

5. **View Results:**
   - Real-time progress tracking during analysis
   - Detailed results with file information
   - Copy results to clipboard functionality

### API Usage

#### Multiple File Analysis
```bash
curl -X POST http://localhost:9000/api/analyze \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf" \
  -F "files=@document3.pdf" \
  -F "prompt=Analyze these documents for compliance requirements"
```

#### Response Format
```json
{
  "filenames": ["document1.pdf", "document2.pdf", "document3.pdf"],
  "file_count": 3,
  "analysis": "Detailed analysis results...",
  "prompt": "Custom prompt used"
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
├── app.py                 # Main Flask application
├── test_upload.py         # Command line interface
├── templates/
│   ├── index.html        # Main upload page
│   ├── status.html       # Processing status page
│   └── result.html       # Results display page
├── uploads/              # Temporary file storage
├── prompt_library.xml    # Prompt configurations (Hebrew)
├── guidelines_sets.xml   # Guidelines definitions
└── README.md            # This file
```

## Technical Details

### Backend Architecture
- **Flask framework** for web server
- **Asynchronous processing** using threading
- **File upload handling** with Unicode filename support
- **OpenAI API integration** using the Responses API
- **Automatic cleanup** of temporary files and uploaded OpenAI files

### OpenAI o3-pro Integration
- **Multiple file support** - uploads all PDFs to OpenAI file storage
- **Combined analysis** - includes all files in a single API request
- **Reasoning effort** - configurable thinking depth (currently set to "medium")
- **Structured responses** - processes and formats model output
- **File cleanup** - automatically deletes files from OpenAI after analysis

### Security Features
- **File type validation** - only accepts PDF files
- **Secure filename handling** - prevents directory traversal
- **Temporary file cleanup** - removes files after processing
- **Error handling** - graceful failure recovery

## Configuration

### Environment Variables
- `OPENAI_API_KEY` or `OPENAI_API_KEY_2`: Your OpenAI API key
- `UPLOAD_FOLDER`: Directory for temporary file storage (default: 'uploads')

### Customization
- **Allowed file types**: Modify `ALLOWED_EXTENSIONS` in `app.py`
- **Default prompts**: Update default prompts in analysis functions
- **UI styling**: Customize CSS in HTML templates
- **Analysis parameters**: Adjust o3-pro reasoning effort and other parameters

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main upload page |
| `/upload` | POST | Web form file upload |
| `/api/analyze` | POST | API file analysis |
| `/api/status/<job_id>` | GET | Check processing status |
| `/result/<job_id>` | GET | View analysis results |

## Error Handling

- **File validation errors** - Invalid file types, empty uploads
- **API errors** - OpenAI API failures, authentication issues
- **Processing errors** - File corruption, analysis failures
- **System errors** - Disk space, permissions, network issues

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
- Check the error messages in the web interface or command line
- Verify your OpenAI API key has access to o3-pro model
- Ensure PDF files are not corrupted or password-protected
- Check system resources for large file uploads

## Changelog

### Latest Version
- ✅ Multiple PDF upload support
- ✅ Enhanced web interface with file previews
- ✅ API support for batch processing
- ✅ Command line interface for terminal users
- ✅ Real-time status tracking
- ✅ Improved error handling and validation
- ✅ Hebrew prompt library integration