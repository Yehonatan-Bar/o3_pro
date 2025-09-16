import os
import tempfile
import threading
import time
import uuid
from openai import OpenAI
from flask import Flask, request, render_template, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}  # o3-pro only accepts PDF files

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# In-memory storage for job status (in production, use Redis or database)
job_status = {}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_files_with_o3_pro(file_paths, custom_prompt=None):
    """Analyze multiple files using OpenAI o3-pro model"""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_2")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    client = OpenAI(api_key=api_key)

    default_prompt = "Read the attached files and give me a concise summary with three key takeaways from each file."
    prompt = custom_prompt if custom_prompt else default_prompt

    uploaded_files = []
    try:
        # 1) Upload all files so the model can reference them
        for file_path in file_paths:
            uploaded = client.files.create(
                file=open(file_path, "rb"),
                purpose="user_data"  # general-purpose file inputs for Responses API
            )
            uploaded_files.append(uploaded)

        # 2) Build content array with all files
        content = []
        for uploaded in uploaded_files:
            content.append({"type": "input_file", "file_id": uploaded.id})
        content.append({"type": "input_text", "text": prompt})

        # 3) Call o3-pro and include all uploaded files as input parts
        resp = client.responses.create(
            model="o3-pro",
            reasoning={"effort": "medium"},  # let o3-pro think a bit; adjust to "high" for tougher tasks
            input=[
                {
                    "role": "user",
                    "content": content
                }
            ]
        )

        # 4) Extract model text output
        out_text = []
        for item in resp.output:
            if getattr(item, "content", None):
                for c in item.content:
                    if getattr(c, "text", None):
                        out_text.append(c.text)

        result = "".join(out_text)

        # Clean up all uploaded files from OpenAI
        for uploaded in uploaded_files:
            try:
                client.files.delete(uploaded.id)
            except:
                pass  # Ignore cleanup errors

        return result

    except Exception as e:
        # Clean up uploaded files on error
        for uploaded in uploaded_files:
            try:
                client.files.delete(uploaded.id)
            except:
                pass
        return f"Error analyzing files: {str(e)}"

def process_files_async(job_id, file_paths, custom_prompt, original_filenames):
    """Process multiple files asynchronously and update job status"""
    try:
        job_status[job_id]['status'] = 'processing'
        job_status[job_id]['message'] = f'Analyzing {len(file_paths)} files with o3-pro...'

        result = analyze_files_with_o3_pro(file_paths, custom_prompt)

        job_status[job_id].update({
            'status': 'completed',
            'result': result,
            'filenames': original_filenames,
            'file_count': len(file_paths),
            'prompt': custom_prompt or "Default prompt used"
        })

        # Clean up the uploaded files
        for file_path in file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)

    except Exception as e:
        job_status[job_id].update({
            'status': 'error',
            'error': str(e)
        })

        # Clean up the uploaded files even if analysis fails
        for file_path in file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        flash('No files selected')
        return redirect(request.url)

    files = request.files.getlist('files')
    custom_prompt = request.form.get('prompt', '').strip()

    if not files or all(file.filename == '' for file in files):
        flash('No files selected')
        return redirect(request.url)

    # Filter valid files
    valid_files = [file for file in files if file and allowed_file(file.filename)]

    if not valid_files:
        flash('No valid PDF files selected. Only PDF files are allowed.')
        return redirect(request.url)

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    file_paths = []
    original_filenames = []

    try:
        # Save all files
        for file in valid_files:
            # Handle Unicode filenames by using a timestamp-based name while preserving extension
            file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            filename = f"upload_{int(time.time())}_{hash(file.filename) % 10000}_{len(file_paths)}.{file_ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            file_paths.append(filepath)
            original_filenames.append(file.filename)

        # Initialize job status
        job_status[job_id] = {
            'status': 'queued',
            'message': f'{len(valid_files)} files uploaded, starting analysis...',
            'created_at': time.time()
        }

        # Start async processing
        thread = threading.Thread(
            target=process_files_async,
            args=(job_id, file_paths, custom_prompt, original_filenames)
        )
        thread.daemon = True
        thread.start()

        # Redirect to status page
        return render_template('status.html', job_id=job_id)

    except Exception as e:
        # Clean up any saved files on error
        for filepath in file_paths:
            if os.path.exists(filepath):
                os.remove(filepath)
        flash(f'Error uploading files: {str(e)}')
        return redirect(url_for('index'))

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for multiple file analysis"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files')
    custom_prompt = request.form.get('prompt', '').strip()

    if not files or all(file.filename == '' for file in files):
        return jsonify({'error': 'No valid files provided'}), 400

    # Filter valid files
    valid_files = [file for file in files if file and allowed_file(file.filename)]

    if not valid_files:
        return jsonify({'error': 'No valid PDF files provided'}), 400

    file_paths = []
    original_filenames = []

    try:
        # Save all files
        for i, file in enumerate(valid_files):
            file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            filename = f"upload_{int(time.time())}_{hash(file.filename) % 10000}_{i}.{file_ext}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            file_paths.append(filepath)
            original_filenames.append(file.filename)

        result = analyze_files_with_o3_pro(file_paths, custom_prompt)

        # Clean up files
        for filepath in file_paths:
            if os.path.exists(filepath):
                os.remove(filepath)

        return jsonify({
            'filenames': original_filenames,
            'file_count': len(original_filenames),
            'analysis': result,
            'prompt': custom_prompt or "Default prompt used"
        })

    except Exception as e:
        # Clean up files on error
        for filepath in file_paths:
            if os.path.exists(filepath):
                os.remove(filepath)
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<job_id>')
def check_status(job_id):
    """Check the status of a processing job"""
    if job_id not in job_status:
        return jsonify({'error': 'Job not found'}), 404

    status = job_status[job_id].copy()

    # Clean up old completed jobs after 1 hour
    if status['status'] in ['completed', 'error'] and time.time() - status.get('created_at', 0) > 3600:
        del job_status[job_id]

    return jsonify(status)

@app.route('/result/<job_id>')
def view_result(job_id):
    """View the result of a completed job"""
    if job_id not in job_status:
        flash('Job not found or expired')
        return redirect(url_for('index'))

    status = job_status[job_id]

    if status['status'] == 'completed':
        # Handle both single file (legacy) and multiple files
        if 'filenames' in status:
            filenames = status['filenames']
            file_count = status.get('file_count', len(filenames))
        else:
            # Legacy single file support
            filenames = [status.get('filename', 'Unknown file')]
            file_count = 1

        return render_template('result.html',
                             filenames=filenames,
                             file_count=file_count,
                             analysis=status['result'],
                             prompt=status['prompt'])
    elif status['status'] == 'error':
        flash(f'Error processing files: {status["error"]}')
        return redirect(url_for('index'))
    else:
        return render_template('status.html', job_id=job_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=True)