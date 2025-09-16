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

def analyze_file_with_o3_pro(file_path, custom_prompt=None):
    """Analyze file using OpenAI o3-pro model (following original script logic)"""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_2")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    client = OpenAI(api_key=api_key)

    default_prompt = "Read the attached file and give me a concise summary with three key takeaways."
    prompt = custom_prompt if custom_prompt else default_prompt

    try:
        # 1) Upload the file so the model can reference it (exactly like original script)
        uploaded = client.files.create(
            file=open(file_path, "rb"),
            purpose="user_data"  # general-purpose file inputs for Responses API
        )

        # 2) Call o3-pro and include the uploaded file as an input part (exactly like original script)
        resp = client.responses.create(
            model="o3-pro",
            reasoning={"effort": "medium"},  # let o3-pro think a bit; adjust to "high" for tougher tasks
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_file", "file_id": uploaded.id},
                        {"type": "input_text", "text": prompt}
                    ]
                }
            ]
        )

        # 3) Extract model text output (exactly like original script)
        out_text = []
        for item in resp.output:
            if getattr(item, "content", None):
                for c in item.content:
                    if getattr(c, "text", None):
                        out_text.append(c.text)

        result = "".join(out_text)

        # Clean up the uploaded file from OpenAI
        try:
            client.files.delete(uploaded.id)
        except:
            pass  # Ignore cleanup errors

        return result

    except Exception as e:
        return f"Error analyzing file: {str(e)}"

def process_file_async(job_id, file_path, custom_prompt, original_filename):
    """Process file asynchronously and update job status"""
    try:
        job_status[job_id]['status'] = 'processing'
        job_status[job_id]['message'] = 'Analyzing file with o3-pro...'

        result = analyze_file_with_o3_pro(file_path, custom_prompt)

        job_status[job_id].update({
            'status': 'completed',
            'result': result,
            'filename': original_filename,
            'prompt': custom_prompt or "Default prompt used"
        })

        # Clean up the uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        job_status[job_id].update({
            'status': 'error',
            'error': str(e)
        })

        # Clean up the uploaded file even if analysis fails
        if os.path.exists(file_path):
            os.remove(file_path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)

    file = request.files['file']
    custom_prompt = request.form.get('prompt', '').strip()

    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Handle Unicode filenames by using a timestamp-based name while preserving extension
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        filename = f"upload_{int(time.time())}_{hash(file.filename) % 10000}.{file_ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Initialize job status
        job_status[job_id] = {
            'status': 'queued',
            'message': 'File uploaded, starting analysis...',
            'created_at': time.time()
        }

        # Start async processing
        thread = threading.Thread(
            target=process_file_async,
            args=(job_id, filepath, custom_prompt, file.filename)
        )
        thread.daemon = True
        thread.start()

        # Redirect to status page
        return render_template('status.html', job_id=job_id)

    else:
        flash('Invalid file type. Allowed types: ' + ', '.join(ALLOWED_EXTENSIONS))
        return redirect(url_for('index'))

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for file analysis"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    custom_prompt = request.form.get('prompt', '').strip()

    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400

    # Handle Unicode filenames by using a timestamp-based name while preserving extension
    import time
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    filename = f"upload_{int(time.time())}_{hash(file.filename) % 10000}.{file_ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        result = analyze_file_with_o3_pro(filepath, custom_prompt)
        os.remove(filepath)

        return jsonify({
            'filename': file.filename,
            'analysis': result,
            'prompt': custom_prompt or "Default prompt used"
        })

    except Exception as e:
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
        return render_template('result.html',
                             filename=status['filename'],
                             analysis=status['result'],
                             prompt=status['prompt'])
    elif status['status'] == 'error':
        flash(f'Error processing file: {status["error"]}')
        return redirect(url_for('index'))
    else:
        return render_template('status.html', job_id=job_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=True)