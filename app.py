import os
import tempfile
import threading
import time
import uuid
import xml.etree.ElementTree as ET
import logging
import concurrent.futures
import json
import pickle
from datetime import datetime
from openai import OpenAI
from flask import Flask, request, render_template, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

# Import mock system
try:
    from simple_mock import get_mock_response
    MOCK_AVAILABLE = True
except ImportError:
    MOCK_AVAILABLE = False
    def get_mock_response(title): return None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)

UPLOAD_FOLDER = 'uploads'
JOBS_FOLDER = 'jobs'
ALLOWED_EXTENSIONS = {'pdf'}  # o3-pro only accepts PDF files

# Mock mode configuration
MOCK_MODE = os.getenv('MOCK_MODE', 'false').lower() == 'true'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(JOBS_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if MOCK_MODE:
    logger.info('🎭 MOCK MODE ENABLED - Using cached responses instead of API calls')
else:
    logger.info('🌐 LIVE MODE - Making real API calls')

# In-memory storage for job status with persistent backup
job_status = {}

# In-memory storage for prompt/response logs
prompt_response_log = []

def log_prompt_response(job_id, guideline_title, guideline_id, prompt, response, timestamp=None):
    """Log prompt and response with metadata"""
    if timestamp is None:
        timestamp = datetime.now().isoformat()

    log_entry = {
        'id': str(uuid.uuid4()),
        'job_id': job_id,
        'guideline_title': guideline_title,
        'guideline_id': guideline_id,
        'prompt': prompt,
        'response': response,
        'timestamp': timestamp,
        'session': job_id  # Use job_id as session identifier
    }

    prompt_response_log.append(log_entry)
    logger.info(f"Logged prompt/response for guideline: {guideline_title} in job: {job_id}")

    # Keep only last 1000 entries to prevent memory issues
    if len(prompt_response_log) > 1000:
        prompt_response_log.pop(0)

def save_job_status(job_id, status):
    """Save job status to disk for persistence"""
    try:
        job_file = os.path.join(JOBS_FOLDER, f"{job_id}.json")
        with open(job_file, 'w') as f:
            json.dump(status, f, default=str, indent=2)
        logger.debug(f"Saved job status for {job_id}")
    except Exception as e:
        logger.error(f"Error saving job status for {job_id}: {e}")

def load_job_status(job_id):
    """Load job status from disk"""
    try:
        job_file = os.path.join(JOBS_FOLDER, f"{job_id}.json")
        if os.path.exists(job_file):
            with open(job_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading job status for {job_id}: {e}")
    return None

def load_all_jobs():
    """Load all persisted jobs on startup"""
    global job_status
    try:
        for filename in os.listdir(JOBS_FOLDER):
            if filename.endswith('.json'):
                job_id = filename[:-5]  # Remove .json extension
                status = load_job_status(job_id)
                if status:
                    job_status[job_id] = status
                    logger.info(f"Recovered job {job_id} with status: {status.get('status', 'unknown')}")
    except Exception as e:
        logger.error(f"Error loading persisted jobs: {e}")

def update_job_status(job_id, updates):
    """Update job status both in memory and on disk"""
    if job_id in job_status:
        job_status[job_id].update(updates)
        save_job_status(job_id, job_status[job_id])
    else:
        logger.warning(f"Attempted to update non-existent job: {job_id}")

# Load any persisted jobs on startup
logger.info("Loading persisted jobs from disk...")
load_all_jobs()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_guidelines_sets():
    """Load guidelines sets from XML file"""
    try:
        logger.info("Loading guidelines sets from XML file")
        tree = ET.parse('guidelines_sets.xml')
        root = tree.getroot()
        guidelines_sets = {}

        for set_elem in root.find('sets').findall('set'):
            set_id = set_elem.get('id')
            set_name = set_elem.get('name')
            set_description = set_elem.get('description')

            guidelines = []
            for guideline in set_elem.find('guidelines').findall('guideline'):
                guideline_data = {
                    'id': guideline.get('id'),
                    'title': guideline.get('title'),
                    'regulation_text': guideline.find('regulation_text').text if guideline.find('regulation_text') is not None else ""
                }
                guidelines.append(guideline_data)

            guidelines_sets[set_id] = {
                'name': set_name,
                'description': set_description,
                'guidelines': guidelines
            }
            logger.info(f"Loaded guideline set '{set_id}' with {len(guidelines)} guidelines")

        logger.info(f"Successfully loaded {len(guidelines_sets)} guideline sets")
        return guidelines_sets
    except Exception as e:
        logger.error(f"Error loading guidelines sets: {e}")
        return {}

def load_prompt_library():
    """Load prompt templates from XML file"""
    try:
        logger.info("Loading prompt library from XML file")
        tree = ET.parse('prompt_library.xml')
        root = tree.getroot()

        general_analysis = root.find('general_analysis_prompt')
        system_prompt = general_analysis.find('system_prompt').text
        general_analysis_text = general_analysis.find('general_analysis').text

        connecting_words = root.find('connecting_words')
        before_guideline = connecting_words.find('before_guideline').text
        after_guideline = connecting_words.find('after_guideline').text

        logger.info("Successfully loaded prompt library")
        return {
            'system_prompt': system_prompt,
            'general_analysis': general_analysis_text,
            'before_guideline': before_guideline,
            'after_guideline': after_guideline
        }
    except Exception as e:
        logger.error(f"Error loading prompt library: {e}")
        # Return working fallback prompts
        return {
            'system_prompt': 'המשימה שלך היא לאשר קיום של הנחיה מסויימת במסמך מסויים, עליך לקרוא את ההנחיה, לראות את הסרטוט, ולהגיב באחת משלושת הדרכים: כן (אם ההנחיה מתקיימת), לא (אם ההנחיה לא מתקיימת), Unknown (אם אין במסמך מידע מתאים)',
            'general_analysis': 'עיין במסמך וכתוב פרוט מסודר של כל הנתונים שאתה יכול להפיק מהמסך. כתוב רק את הנתונים שניתן להפיק בוודאות ובבירור מתוך המסמך. בדוק היטב את הנתונים והתעלם מנתונים שלא ברורים לחלוטין.',
            'before_guideline': 'זאת ההנחיה שצריך לבדוק:',
            'after_guideline': 'עד כאן ההנחיה'
        }

def analyze_files_with_o3_pro(file_paths, custom_prompt=None):
    """Analyze multiple files using OpenAI o3-pro model"""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_2")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    client = OpenAI(api_key=api_key, timeout=1200.0)  # 20 minutes timeout for o3-pro

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
            reasoning={"effort": "high"},  # let o3-pro think a bit; adjust to "high" for tougher tasks
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

def analyze_files_with_guidelines(file_paths, guideline_set_id, job_id=None):
    """Analyze multiple files using guidelines from XML"""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_2")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    client = OpenAI(api_key=api_key, timeout=1200.0)  # 20 minutes timeout for o3-pro

    # Load guidelines and prompts
    guidelines_sets = load_guidelines_sets()
    prompt_library = load_prompt_library()

    if guideline_set_id not in guidelines_sets:
        raise ValueError(f"Guidelines set '{guideline_set_id}' not found")

    guideline_set = guidelines_sets[guideline_set_id]
    guidelines = guideline_set['guidelines']

    uploaded_files = []
    guideline_results = []

    try:
        # Upload all files first
        for file_path in file_paths:
            uploaded = client.files.create(
                file=open(file_path, "rb"),
                purpose="user_data"
            )
            uploaded_files.append(uploaded)

        # Process each guideline
        for i, guideline in enumerate(guidelines):
            if job_id and job_id in job_status:
                job_status[job_id]['message'] = f'Analyzing guideline {i+1}/{len(guidelines)}: {guideline["title"]}'

            # Construct the prompt
            prompt_parts = [
                prompt_library['system_prompt'],
                prompt_library['general_analysis'],
                prompt_library['before_guideline'],
                guideline['regulation_text'],
                prompt_library['after_guideline']
            ]

            combined_prompt = '\n\n'.join(part for part in prompt_parts if part.strip())

            # Build content array with all files and the guideline-specific prompt
            content = []
            for uploaded in uploaded_files:
                content.append({"type": "input_file", "file_id": uploaded.id})
            content.append({"type": "input_text", "text": combined_prompt})

            # Call o3-pro for this guideline
            resp = client.responses.create(
                model="o3-pro",
                reasoning={"effort": "high"},
                input=[
                    {
                        "role": "user",
                        "content": content
                    }
                ]
            )

            # Extract response
            out_text = []
            for item in resp.output:
                if getattr(item, "content", None):
                    for c in item.content:
                        if getattr(c, "text", None):
                            out_text.append(c.text)

            result_text = "".join(out_text)

            # Extract the compliance answer (כן/לא/Unknown)
            compliance_status = "Unknown"
            if "כן" in result_text:
                compliance_status = "כן"
            elif "לא" in result_text:
                compliance_status = "לא"

            guideline_results.append({
                'guideline_id': guideline['id'],
                'title': guideline['title'],
                'compliance_status': compliance_status,
                'analysis': result_text,
                'regulation_text': guideline['regulation_text']
            })

        # Clean up uploaded files
        for uploaded in uploaded_files:
            try:
                client.files.delete(uploaded.id)
            except:
                pass

        return {
            'guideline_set_name': guideline_set['name'],
            'guideline_results': guideline_results,
            'summary': generate_summary_report(guideline_results)
        }

    except Exception as e:
        # Clean up uploaded files on error
        for uploaded in uploaded_files:
            try:
                client.files.delete(uploaded.id)
            except:
                pass
        raise e

def generate_summary_report(guideline_results):
    """Generate a summary report from individual guideline results"""
    total = len(guideline_results)
    compliant = sum(1 for r in guideline_results if r['compliance_status'] == 'כן')
    non_compliant = sum(1 for r in guideline_results if r['compliance_status'] == 'לא')
    unknown = sum(1 for r in guideline_results if r['compliance_status'] == 'Unknown')

    summary = f"""
# סיכום דוח ניתוח הנחיות

## תוצאות כלליות:
- סך הכל הנחיות שנבדקו: {total}
- עמידה בדרישות (כן): {compliant}
- אי עמידה בדרישות (לא): {non_compliant}
- לא ברור/אין מידע (Unknown): {unknown}

## תוצאות מפורטות:
"""

    for result in guideline_results:
        summary += f"\n### {result['title']}\n"
        summary += f"**תוצאה:** {result['compliance_status']}\n"
        if result['analysis'].strip():
            summary += f"**פירוט:** {result['analysis'][:200]}{'...' if len(result['analysis']) > 200 else ''}\n"
        summary += "\n---\n"

    return summary

def analyze_single_guideline(uploaded_files, guideline, prompt_library, guideline_index, total_guidelines, job_id=None, delay_seconds=10):
    """Analyze a single guideline with delay and error handling"""

    guideline_id = guideline['id']
    guideline_title = guideline['title']

    try:
        logger.info(f"Starting analysis for guideline {guideline_index + 1}/{total_guidelines}: {guideline_title}")

        # Check for mock response first
        if MOCK_MODE and MOCK_AVAILABLE:
            mock_response = get_mock_response(guideline_title)
            if mock_response:
                logger.info(f"🎭 Using mock response for: {guideline_title}")
                result_text = mock_response

                # Skip API call and go directly to result processing
                # Log the mock prompt and response
                combined_prompt = "Mock prompt for " + guideline_title
                log_prompt_response(
                    job_id=job_id,
                    guideline_title=guideline_title,
                    guideline_id=guideline_id,
                    prompt=combined_prompt,
                    response=result_text
                )

                # Process the mock response (continue to result processing)
                # Extract JSON from response and map to compliance status
                compliance_status = "Unknown"
                explanation = ""

                try:
                    import re
                    json_start = result_text.find('{')
                    json_end = result_text.rfind('}') + 1

                    if json_start >= 0 and json_end > json_start:
                        json_str = result_text[json_start:json_end]
                        json_obj = json.loads(json_str)
                        result_value = json_obj.get('result', -1)
                        explanation = json_obj.get('explanation', '')

                        # Extract new fields from JSON response
                        status = json_obj.get('status', '')
                        status_detail = json_obj.get('status_detail', '')
                        category = json_obj.get('category', '')
                        issue_number = json_obj.get('issue_number', '')
                        severity = json_obj.get('severity', '')

                        if result_value == 1:
                            compliance_status = "כן"
                        elif result_value == 0:
                            compliance_status = "לא"
                        else:
                            compliance_status = "Unknown"

                        logger.info(f"Mock response parsed: {compliance_status}, result_value: {result_value}, status: {status}")
                except Exception as e:
                    logger.warning(f"Could not parse mock JSON: {e}")
                    # Fallback: try to extract explanation from JSON manually
                    try:
                        explanation_match = re.search(r'"explanation":\s*"([^"]*)"', result_text)
                        if explanation_match:
                            explanation = explanation_match.group(1)
                        result_match = re.search(r'"result":\s*(-?\d+)', result_text)
                        if result_match:
                            result_value = int(result_match.group(1))
                            if result_value == 1:
                                compliance_status = "כן"
                            elif result_value == 0:
                                compliance_status = "לא"
                            else:
                                compliance_status = "Unknown"
                    except Exception as fallback_error:
                        logger.warning(f"Fallback parsing also failed: {fallback_error}")
                        # Last resort: search for compliance keywords in the text
                        if "כן" in result_text:
                            compliance_status = "כן"
                        elif "לא" in result_text:
                            compliance_status = "לא"
                        # If no explanation found, try to extract it from result_text
                        if not explanation:
                            explanation = result_text.replace('{', '').replace('}', '').replace('"', '').strip()

                # Ensure we always have explanation text and never show JSON
                if not explanation:
                    explanation = "אירעה שגיאה בעיבוד התגובה"

                # Return mock result with new fields
                return {
                    'guideline_id': guideline['id'],
                    'title': guideline['title'],
                    'compliance_status': compliance_status,
                    'analysis': explanation,  # Always use explanation, never full JSON
                    'explanation': explanation,
                    'regulation_text': guideline['regulation_text'],
                    'status': locals().get('status', ''),
                    'status_detail': locals().get('status_detail', ''),
                    'category': locals().get('category', ''),
                    'issue_number': locals().get('issue_number', ''),
                    'severity': locals().get('severity', ''),
                    'processing_time': time.time(),
                    'completed_at': datetime.now().isoformat()
                }

        # Real API mode - add delay before each API call
        logger.info(f"Waiting {delay_seconds} seconds before processing guideline {guideline_index + 1}")
        time.sleep(delay_seconds)

        # Update job status for this specific guideline with persistence
        if job_id and job_id in job_status:
            current_guidelines = job_status[job_id].get('current_guidelines', {})
            current_guidelines[guideline_id] = {
                'status': 'processing',
                'title': guideline_title,
                'index': guideline_index + 1,
                'total': total_guidelines,
                'started_at': datetime.now().isoformat(),
                'last_heartbeat': datetime.now().isoformat()
            }
            update_job_status(job_id, {
                'current_guidelines': current_guidelines
            })

        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_2")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        client = OpenAI(api_key=api_key, timeout=1200.0)  # 20 minutes timeout for o3-pro high quality analysis

        # Construct the prompt
        prompt_parts = [
            prompt_library['system_prompt'],
            prompt_library['before_guideline'],
            guideline['regulation_text'],
            prompt_library['after_guideline']
        ]

        combined_prompt = '\n\n'.join(part for part in prompt_parts if part.strip())

        # Build content array with all files and the guideline-specific prompt
        content = []
        for uploaded in uploaded_files:
            content.append({"type": "input_file", "file_id": uploaded.id})
        content.append({"type": "input_text", "text": combined_prompt})

        logger.info(f"Sending API request for guideline: {guideline_title}")

        # Start heartbeat thread to keep job alive during long API call
        heartbeat_active = threading.Event()
        heartbeat_active.set()

        def heartbeat_updater():
            while heartbeat_active.is_set():
                try:
                    if job_id and job_id in job_status:
                        current_guidelines = job_status[job_id].get('current_guidelines', {})
                        if guideline_id in current_guidelines:
                            current_guidelines[guideline_id]['last_heartbeat'] = datetime.now().isoformat()
                            update_job_status(job_id, {'current_guidelines': current_guidelines})
                    time.sleep(30)  # Heartbeat every 30 seconds
                except Exception as e:
                    logger.error(f"Heartbeat error for {guideline_id}: {e}")

        heartbeat_thread = threading.Thread(target=heartbeat_updater, daemon=True)
        heartbeat_thread.start()

        try:
            # Call o3-pro for this guideline with retry logic
            max_retries = 3
            retry_count = 0

            while retry_count < max_retries:
                try:
                    resp = client.responses.create(
                        model="o3-pro",
                        reasoning={"effort": "high"},
                        input=[
                            {
                                "role": "user",
                                "content": content
                            }
                        ]
                    )
                    break  # Success - exit retry loop

                except Exception as api_error:
                    retry_count += 1
                    error_msg = str(api_error)

                    if "502" in error_msg or "Bad Gateway" in error_msg:
                        if retry_count < max_retries:
                            wait_time = retry_count * 30  # Progressive backoff: 30s, 60s, 90s
                            logger.warning(f"OpenAI API 502 error for {guideline_title}, retry {retry_count}/{max_retries} in {wait_time}s")
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"OpenAI API failed after {max_retries} retries for {guideline_title}: {error_msg}")
                            raise api_error
                    else:
                        # Non-502 error - don't retry
                        logger.error(f"OpenAI API non-retryable error for {guideline_title}: {error_msg}")
                        raise api_error

            # Stop heartbeat
            heartbeat_active.clear()

            # Extract response
            out_text = []
            for item in resp.output:
                if getattr(item, "content", None):
                    for c in item.content:
                        if getattr(c, "text", None):
                            out_text.append(c.text)

            result_text = "".join(out_text)

            # Log the prompt and response
            log_prompt_response(
                job_id=job_id,
                guideline_title=guideline_title,
                guideline_id=guideline_id,
                prompt=combined_prompt,
                response=result_text
            )

            # Extract the compliance answer (כן/לא/Unknown)
            compliance_status = "Unknown"
            explanation = result_text  # Default to full text

            # Try to parse JSON response first (same logic as mock processing)
            status = ""
            status_detail = ""
            category = ""
            issue_number = ""
            severity = ""

            try:
                import re
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1

                if json_start >= 0 and json_end > json_start:
                    json_str = result_text[json_start:json_end]
                    json_obj = json.loads(json_str)
                    result_value = json_obj.get('result', -1)
                    extracted_explanation = json_obj.get('explanation', '')

                    # Extract new fields from JSON response
                    status = json_obj.get('status', '')
                    status_detail = json_obj.get('status_detail', '')
                    category = json_obj.get('category', '')
                    issue_number = json_obj.get('issue_number', '')
                    severity = json_obj.get('severity', '')

                    if result_value == 1:
                        compliance_status = "כן"
                    elif result_value == 0:
                        compliance_status = "לא"
                    else:
                        compliance_status = "Unknown"

                    # Use extracted explanation if available
                    if extracted_explanation:
                        explanation = extracted_explanation

                    logger.info(f"Real API response parsed: {compliance_status}, result_value: {result_value}, status: {status}")
                else:
                    # Fallback to text-based search
                    if "כן" in result_text:
                        compliance_status = "כן"
                    elif "לא" in result_text:
                        compliance_status = "לא"
                    logger.info(f"Real API response using text search: {compliance_status}")

            except Exception as e:
                logger.warning(f"Could not parse real API JSON: {e}")
                # Fallback to original text-based logic
                if "כן" in result_text:
                    compliance_status = "כן"
                elif "לא" in result_text:
                    compliance_status = "לא"
                logger.info(f"Real API response fallback: {compliance_status}")

            guideline_result = {
                'guideline_id': guideline['id'],
                'title': guideline['title'],
                'compliance_status': compliance_status,
                'analysis': explanation,  # Use explanation instead of full result_text
                'regulation_text': guideline['regulation_text'],
                'status': status,
                'status_detail': status_detail,
                'category': category,
                'issue_number': issue_number,
                'severity': severity,
                'processing_time': time.time(),
                'completed_at': datetime.now().isoformat()
            }

            # Update job status for completion with persistence
            if job_id and job_id in job_status:
                current_guidelines = job_status[job_id].get('current_guidelines', {})
                current_guidelines[guideline_id].update({
                    'status': 'completed',
                    'result': compliance_status,
                    'completed_at': datetime.now().isoformat(),
                    'analysis': result_text
                })
                update_job_status(job_id, {'current_guidelines': current_guidelines})

        except Exception as api_error:
            # Stop heartbeat on error
            heartbeat_active.clear()
            raise api_error

        logger.info(f"Successfully completed analysis for guideline: {guideline_title} - Result: {compliance_status}")
        return guideline_result

    except Exception as e:
        error_msg = f"Error analyzing guideline {guideline_title}: {str(e)}"
        logger.error(error_msg)

        # Update job status for error with persistence
        if job_id and job_id in job_status:
            current_guidelines = job_status[job_id].get('current_guidelines', {})
            current_guidelines[guideline_id] = {
                'status': 'error',
                'title': guideline_title,
                'error': str(e),
                'index': guideline_index + 1,
                'total': total_guidelines,
                'failed_at': datetime.now().isoformat()
            }
            update_job_status(job_id, {'current_guidelines': current_guidelines})

        return {
            'guideline_id': guideline['id'],
            'title': guideline['title'],
            'compliance_status': 'Error',
            'analysis': f"Error occurred during analysis: {str(e)}",
            'regulation_text': guideline['regulation_text'],
            'error': True
        }

def analyze_files_with_guidelines_parallel(file_paths, guideline_set_id, job_id=None, max_workers=3):
    """Analyze multiple files using guidelines from XML with parallel processing"""
    logger.info(f"Starting parallel guidelines analysis for set: {guideline_set_id}")

    try:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY_2")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        client = OpenAI(api_key=api_key, timeout=1200.0)

        # Load guidelines and prompts
        guidelines_sets = load_guidelines_sets()
        prompt_library = load_prompt_library()

        if guideline_set_id not in guidelines_sets:
            raise ValueError(f"Guidelines set '{guideline_set_id}' not found")

        guideline_set = guidelines_sets[guideline_set_id]
        guidelines = guideline_set['guidelines']

        logger.info(f"Found {len(guidelines)} guidelines to process in parallel (max_workers={max_workers})")

        uploaded_files = []
        guideline_results = []

        try:
            # Upload all files first
            logger.info("Uploading files to OpenAI...")
            for file_path in file_paths:
                uploaded = client.files.create(
                    file=open(file_path, "rb"),
                    purpose="user_data"
                )
                uploaded_files.append(uploaded)
                logger.info(f"Uploaded file: {file_path}")

            # Initialize job status for parallel processing with persistence
            if job_id and job_id in job_status:
                update_job_status(job_id, {
                    'message': f'Processing {len(guidelines)} guidelines in parallel...',
                    'total_guidelines': len(guidelines),
                    'completed_guidelines': 0,
                    'current_guidelines': {},
                    'processing_started_at': datetime.now().isoformat()
                })

            # Process guidelines in parallel with limited workers
            logger.info(f"Starting parallel processing with {max_workers} workers")

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all guideline analysis tasks
                future_to_guideline = {}
                for i, guideline in enumerate(guidelines):
                    future = executor.submit(
                        analyze_single_guideline,
                        uploaded_files,
                        guideline,
                        prompt_library,
                        i,
                        len(guidelines),
                        job_id
                    )
                    future_to_guideline[future] = guideline
                    logger.info(f"Submitted guideline {i+1}/{len(guidelines)}: {guideline['title']}")

                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_guideline):
                    guideline = future_to_guideline[future]
                    try:
                        result = future.result()
                        guideline_results.append(result)

                        # Update job status with persistence
                        if job_id and job_id in job_status:
                            update_job_status(job_id, {
                                'completed_guidelines': len(guideline_results),
                                'message': f'Completed {len(guideline_results)}/{len(guidelines)} guidelines',
                                'last_update': datetime.now().isoformat()
                            })

                        logger.info(f"Completed guideline: {guideline['title']} - Status: {result.get('compliance_status', 'Unknown')}")

                    except Exception as exc:
                        error_msg = f"Guideline {guideline['title']} generated an exception: {exc}"
                        logger.error(error_msg)

                        # Add error result
                        error_result = {
                            'guideline_id': guideline['id'],
                            'title': guideline['title'],
                            'compliance_status': 'Error',
                            'analysis': f"Error occurred during analysis: {str(exc)}",
                            'regulation_text': guideline['regulation_text'],
                            'error': True
                        }
                        guideline_results.append(error_result)

            # Clean up uploaded files
            logger.info("Cleaning up uploaded files...")
            for uploaded in uploaded_files:
                try:
                    client.files.delete(uploaded.id)
                except Exception as cleanup_error:
                    logger.warning(f"Error cleaning up file {uploaded.id}: {cleanup_error}")

            # Sort results by original order
            guideline_results.sort(key=lambda x: next((i for i, g in enumerate(guidelines) if g['id'] == x['guideline_id']), 999))

            result = {
                'guideline_set_name': guideline_set['name'],
                'guideline_results': guideline_results,
                'summary': generate_summary_report(guideline_results)
            }

            logger.info(f"Successfully completed parallel analysis of {len(guideline_results)} guidelines")
            return result

        except Exception as e:
            # Clean up uploaded files on error
            logger.error(f"Error during parallel processing: {e}")
            for uploaded in uploaded_files:
                try:
                    client.files.delete(uploaded.id)
                except:
                    pass
            raise e

    except Exception as e:
        logger.error(f"Failed to start parallel guidelines analysis: {e}")
        raise e

def process_files_async(job_id, file_paths, custom_prompt, original_filenames, guideline_set_id=None):
    """Process multiple files asynchronously and update job status"""
    logger.info(f"Starting async processing for job {job_id}, files: {len(file_paths)}, guideline_set: {guideline_set_id}")
    try:
        update_job_status(job_id, {'status': 'processing'})

        if guideline_set_id:
            # Use parallel guideline-based analysis
            logger.info(f"Starting parallel guideline analysis for job {job_id}")
            job_status[job_id]['message'] = f'Starting parallel guideline analysis for {len(file_paths)} files...'
            result = analyze_files_with_guidelines_parallel(file_paths, guideline_set_id, job_id)

            update_job_status(job_id, {
                'status': 'completed',
                'result': result,
                'filenames': original_filenames,
                'file_count': len(file_paths),
                'analysis_type': 'guidelines',
                'guideline_set_id': guideline_set_id,
                'completed_at': datetime.now().isoformat()
            })
        else:
            # Use traditional o3-pro analysis
            update_job_status(job_id, {'message': f'Analyzing {len(file_paths)} files with o3-pro...'})
            result = analyze_files_with_o3_pro(file_paths, custom_prompt)

            update_job_status(job_id, {
                'status': 'completed',
                'result': result,
                'filenames': original_filenames,
                'file_count': len(file_paths),
                'prompt': custom_prompt or "Default prompt used",
                'analysis_type': 'traditional',
                'completed_at': datetime.now().isoformat()
            })

        # Clean up the uploaded files
        logger.info(f"Cleaning up uploaded files for job {job_id}")
        for file_path in file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)

        logger.info(f"Successfully completed processing for job {job_id}")

    except Exception as e:
        logger.error(f"Error processing files for job {job_id}: {str(e)}")
        update_job_status(job_id, {
            'status': 'error',
            'error': str(e),
            'failed_at': datetime.now().isoformat()
        })

        # Clean up the uploaded files even if analysis fails
        logger.info(f"Cleaning up files after error for job {job_id}")
        for file_path in file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)

@app.route('/')
def index():
    guidelines_sets = load_guidelines_sets()
    return render_template('index.html', guidelines_sets=guidelines_sets)

@app.route('/logs')
def logs_page():
    return render_template('logs.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        flash('No files selected')
        return redirect(request.url)

    files = request.files.getlist('files')
    custom_prompt = request.form.get('prompt', '').strip()
    guideline_set_id = request.form.get('guideline_set', '').strip()

    logger.info(f"Upload request - Files: {len(files)}, Guideline set: '{guideline_set_id}', Custom prompt: {'Yes' if custom_prompt else 'No'}")

    if not files or all(file.filename == '' for file in files):
        flash('No files selected')
        return redirect(request.url)

    # Validate guideline set selection
    if not guideline_set_id:
        flash('Please select a guidelines set')
        return redirect(request.url)

    # Validate that the guideline set exists
    guidelines_sets = load_guidelines_sets()
    if guideline_set_id not in guidelines_sets:
        flash(f'Invalid guidelines set selected: {guideline_set_id}')
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

        # Initialize job status with persistence
        logger.info(f"Initializing job {job_id} with {len(valid_files)} files and guideline set '{guideline_set_id}'")

        job_status[job_id] = {
            'status': 'queued',
            'message': f'{len(valid_files)} files uploaded, starting analysis...',
            'created_at': time.time(),
            'guideline_set_id': guideline_set_id,
            'filenames': original_filenames,
            'file_count': len(valid_files)
        }

        try:
            save_job_status(job_id, job_status[job_id])
            logger.info(f"Successfully saved initial job status for {job_id}")
        except Exception as save_error:
            logger.error(f"Failed to save job status for {job_id}: {save_error}")
            # Continue anyway - job will work in memory

        # Start async processing
        thread = threading.Thread(
            target=process_files_async,
            args=(job_id, file_paths, custom_prompt, original_filenames, guideline_set_id)
        )
        thread.daemon = True
        thread.start()

        # Redirect to status page
        return render_template('status.html', job_id=job_id)

    except Exception as e:
        logger.error(f"Error during file upload for job {job_id}: {str(e)}")
        # Clean up any saved files on error
        for filepath in file_paths:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    logger.debug(f"Cleaned up file: {filepath}")
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up file {filepath}: {cleanup_error}")

        # Clean up job status if it was created
        if job_id in job_status:
            del job_status[job_id]

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
    try:
        # Try to get from memory first
        if job_id in job_status:
            status = job_status[job_id].copy()
        else:
            # Try to load from disk
            logger.info(f"Job {job_id} not in memory, trying to load from disk")
            status = load_job_status(job_id)
            if status:
                job_status[job_id] = status
                logger.info(f"Loaded job {job_id} from disk")
            else:
                logger.warning(f"Job {job_id} not found in memory or disk")
                return jsonify({'error': 'Job not found'}), 404

        # Clean up old completed jobs after 1 hour
        if status['status'] in ['completed', 'error'] and time.time() - status.get('created_at', 0) > 3600:
            if job_id in job_status:
                del job_status[job_id]
            # Also clean up from disk
            try:
                job_file = os.path.join(JOBS_FOLDER, f"{job_id}.json")
                if os.path.exists(job_file):
                    os.remove(job_file)
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up job file {job_id}: {cleanup_error}")

        return jsonify(status)

    except Exception as e:
        logger.error(f"Error checking status for job {job_id}: {e}")
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

@app.route('/result/<job_id>')
def view_result(job_id):
    """View the result of a completed job"""
    try:
        # Try to get from memory first
        if job_id in job_status:
            status = job_status[job_id]
        else:
            # Try to load from disk
            logger.info(f"Result view: Job {job_id} not in memory, trying to load from disk")
            status = load_job_status(job_id)
            if status:
                job_status[job_id] = status
                logger.info(f"Result view: Loaded job {job_id} from disk")
            else:
                logger.warning(f"Result view: Job {job_id} not found")
                flash('Job not found or expired')
                return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Error loading result for job {job_id}: {e}")
        flash(f'Error loading job results: {str(e)}')
        return redirect(url_for('index'))

    if status['status'] == 'completed':
        # Handle both single file (legacy) and multiple files
        if 'filenames' in status:
            filenames = status['filenames']
            file_count = status.get('file_count', len(filenames))
        else:
            # Legacy single file support
            filenames = [status.get('filename', 'Unknown file')]
            file_count = 1

        analysis_type = status.get('analysis_type', 'traditional')

        if analysis_type == 'guidelines':
            return render_template('result.html',
                                 filenames=filenames,
                                 file_count=file_count,
                                 analysis_type=analysis_type,
                                 result=status['result'],
                                 guideline_set_id=status.get('guideline_set_id'))
        else:
            return render_template('result.html',
                                 filenames=filenames,
                                 file_count=file_count,
                                 analysis_type=analysis_type,
                                 analysis=status['result'],
                                 prompt=status.get('prompt', 'Default prompt used'))
    elif status['status'] == 'error':
        flash(f'Error processing files: {status["error"]}')
        return redirect(url_for('index'))
    else:
        return render_template('status.html', job_id=job_id)

@app.route('/api/recover/<job_id>', methods=['POST'])
def recover_job(job_id):
    """Recover and resume an interrupted job"""
    try:
        logger.info(f"Attempting to recover job: {job_id}")

        # Load job from disk if not in memory
        if job_id not in job_status:
            status = load_job_status(job_id)
            if status:
                job_status[job_id] = status
                logger.info(f"Loaded job {job_id} from disk")
            else:
                return jsonify({'error': 'Job not found'}), 404

        current_status = job_status[job_id]

        # Check if job is recoverable
        if current_status.get('status') == 'completed':
            return jsonify({'message': 'Job already completed', 'status': current_status})

        if current_status.get('status') == 'processing' and current_status.get('analysis_type') == 'guidelines':
            # Job was processing guidelines - check what's completed
            current_guidelines = current_status.get('current_guidelines', {})
            completed_count = len([g for g in current_guidelines.values() if g.get('status') == 'completed'])
            total_count = current_status.get('total_guidelines', 0)

            logger.info(f"Job {job_id} recovery: {completed_count}/{total_count} guidelines completed")

            if completed_count == total_count:
                # All guidelines completed, just need to finalize
                guidelines_sets = load_guidelines_sets()
                guideline_set_id = current_status.get('guideline_set_id')

                if guideline_set_id in guidelines_sets:
                    guideline_set = guidelines_sets[guideline_set_id]

                    # Rebuild results from completed guidelines
                    guideline_results = []
                    for guideline in guideline_set['guidelines']:
                        guideline_id = guideline['id']
                        if guideline_id in current_guidelines and current_guidelines[guideline_id].get('status') == 'completed':
                            guideline_results.append({
                                'guideline_id': guideline_id,
                                'title': guideline['title'],
                                'compliance_status': current_guidelines[guideline_id].get('result', 'Unknown'),
                                'analysis': current_guidelines[guideline_id].get('analysis', ''),
                                'regulation_text': guideline['regulation_text']
                            })

                    result = {
                        'guideline_set_name': guideline_set['name'],
                        'guideline_results': guideline_results,
                        'summary': generate_summary_report(guideline_results)
                    }

                    # Mark as completed
                    update_job_status(job_id, {
                        'status': 'completed',
                        'result': result,
                        'recovered_at': datetime.now().isoformat()
                    })

                    logger.info(f"Successfully recovered and completed job {job_id}")
                    return jsonify({'message': 'Job recovered and completed', 'status': job_status[job_id]})

            # Job is still processing, return current status
            update_job_status(job_id, {
                'message': f'Job recovered - {completed_count}/{total_count} guidelines completed',
                'recovered_at': datetime.now().isoformat()
            })

            return jsonify({'message': 'Job recovered, still processing', 'status': job_status[job_id]})

        return jsonify({'message': 'Job status unclear, cannot recover', 'status': current_status})

    except Exception as e:
        logger.error(f"Error recovering job {job_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs')
def list_jobs():
    """List all jobs (in memory and on disk)"""
    try:
        all_jobs = {}

        # Add in-memory jobs
        for job_id, status in job_status.items():
            all_jobs[job_id] = {
                'status': status.get('status'),
                'created_at': status.get('created_at'),
                'analysis_type': status.get('analysis_type'),
                'in_memory': True
            }

        # Add disk-only jobs
        try:
            for filename in os.listdir(JOBS_FOLDER):
                if filename.endswith('.json'):
                    job_id = filename[:-5]
                    if job_id not in all_jobs:
                        disk_status = load_job_status(job_id)
                        if disk_status:
                            all_jobs[job_id] = {
                                'status': disk_status.get('status'),
                                'created_at': disk_status.get('created_at'),
                                'analysis_type': disk_status.get('analysis_type'),
                                'in_memory': False
                            }
        except Exception as e:
            logger.error(f"Error reading jobs directory: {e}")

        return jsonify(all_jobs)

    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/prompt-logs')
def get_prompt_logs():
    """Get prompt/response logs with optional filtering and sorting"""
    try:
        sort_by = request.args.get('sort_by', 'timestamp')  # timestamp, text, session, guideline_title
        sort_order = request.args.get('sort_order', 'desc')  # asc, desc
        session_filter = request.args.get('session', '')
        search_text = request.args.get('search', '')
        limit = int(request.args.get('limit', 100))

        # Filter logs
        filtered_logs = prompt_response_log.copy()

        if session_filter:
            filtered_logs = [log for log in filtered_logs if log['session'] == session_filter]

        if search_text:
            search_lower = search_text.lower()
            filtered_logs = [
                log for log in filtered_logs
                if search_lower in log['prompt'].lower() or
                   search_lower in log['response'].lower() or
                   search_lower in log['guideline_title'].lower()
            ]

        # Sort logs
        reverse = sort_order == 'desc'

        if sort_by == 'timestamp':
            filtered_logs.sort(key=lambda x: x['timestamp'], reverse=reverse)
        elif sort_by == 'text':
            filtered_logs.sort(key=lambda x: x['guideline_title'].lower(), reverse=reverse)
        elif sort_by == 'session':
            filtered_logs.sort(key=lambda x: x['session'], reverse=reverse)
        elif sort_by == 'guideline_title':
            filtered_logs.sort(key=lambda x: x['guideline_title'].lower(), reverse=reverse)

        # Limit results
        filtered_logs = filtered_logs[:limit]

        # Get unique sessions for filter dropdown
        sessions = list(set(log['session'] for log in prompt_response_log))
        sessions.sort()

        return jsonify({
            'logs': filtered_logs,
            'total_count': len(prompt_response_log),
            'filtered_count': len(filtered_logs),
            'sessions': sessions
        })

    except Exception as e:
        logger.error(f"Error retrieving prompt logs: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=True)