"""
Flask Application - Web interface for AgenticAI
Intelligent multi-modal data labeling platform with TRUE AGENTIC SYSTEM
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, request, jsonify, render_template, send_from_directory, has_request_context
from werkzeug.utils import secure_filename
from orchestrator_agentic import AgenticOrchestrator  # NEW: Using agentic orchestrator
from config import Config
import uuid
import atexit

# Try to import CORS, but make it optional
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False

# Import utilities
from utils.logger import get_system_logger
from utils.rate_limiter import rate_limit
from utils.background_tasks import get_task_manager, TaskStatus
from utils.resource_manager import get_resource_manager
from utils.api_utils import handle_api_error

# Initialize logging
logger = get_system_logger()

# Get the project root directory (parent of src)
project_root = Path(__file__).parent.parent
app = Flask(__name__, 
            template_folder=str(project_root / 'templates'), 
            static_folder=str(project_root / 'static'))
# Use absolute path for upload folder
upload_folder = project_root / Config.UPLOAD_FOLDER
app.config['UPLOAD_FOLDER'] = str(upload_folder)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Enable CORS for all routes (can be restricted in production)
if CORS_AVAILABLE:
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    logger.info("CORS enabled via flask-cors")
else:
    logger.warning("flask-cors not installed. CORS support will use manual headers.")
    # Add basic CORS headers manually if flask-cors is not available
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

# Initialize utilities
resource_manager = get_resource_manager()
task_manager = get_task_manager()

# Register cleanup on exit
atexit.register(lambda: task_manager.stop())

# Allowed extensions
ALLOWED_EXTENSIONS = {
    'text_document': {'pdf', 'txt', 'docx', 'doc', 'csv', 'xlsx', 'xls'},
    'image': {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'svg'},
    'audio': {'mp3', 'wav', 'flac', 'm4a', 'aac', 'ogg', 'wma', 'mp4', 'avi', 'mov', 'mkv'}
}

def allowed_file(filename):
    """Check if file extension is allowed."""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return any(ext in extensions for extensions in ALLOWED_EXTENSIONS.values())

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    import traceback
    error_trace = traceback.format_exc()
    logger.exception("Internal server error", error=str(error), traceback=error_trace)
    
    # Always return JSON for API consistency
    # Don't try to render error.html as it may not exist
    return jsonify({
        'error': 'Internal server error',
        'message': str(error),
        'traceback': error_trace if app.debug else None
    }), 500

# Note: We don't use @app.errorhandler(Exception) as it's too broad
# and can interfere with Flask's internal error handling
# Individual routes handle their own exceptions

@app.route('/')
def home():
    """Serve the home page."""
    try:
        return render_template('home.html')
    except Exception as e:
        logger.exception("Error rendering home template", error=str(e))
        return jsonify({'error': 'Failed to load home page', 'message': str(e)}), 500

@app.route('/labeling')
def labeling():
    """Serve the labeling page."""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.exception("Error rendering labeling template", error=str(e))
        return jsonify({'error': 'Failed to load labeling page', 'message': str(e)}), 500

def process_file_task(file_path: str, openai_api_key: str, deepseek_api_key: str, output_dir: str = None):
    """
    Background task for processing files.
    
    Args:
        file_path: Path to file
        openai_api_key: OpenAI API key
        deepseek_api_key: DeepSeek API key
        output_dir: Output directory (defaults to project_root/output)
        
    Returns:
        Processing result
    """
    # Use absolute path for output directory
    if output_dir is None:
        output_dir = str(project_root / 'output')
    elif not os.path.isabs(output_dir):
        output_dir = str(project_root / output_dir)
    
    try:
        # Track file for cleanup
        resource_manager.track_file(file_path, auto_cleanup=True)
        
        logger.info("Starting file processing", file_path=file_path)
        
        # Initialize agentic orchestrator
        orchestrator = AgenticOrchestrator(
            deepseek_api_key=deepseek_api_key,
            openai_api_key=openai_api_key
        )
        
        # Process file without timeout
        result = orchestrator.process_file(
            file_path=file_path,
            output_dir=output_dir
        )
        
        logger.info("File processing completed", file_path=file_path, success=result.get('success', False))
        
        return result
        
    except Exception as e:
        error_info = handle_api_error(e)
        logger.error("File processing failed", file_path=file_path, error=str(e), error_type=error_info['error_type'])
        return {
            'error': str(e),
            'error_type': error_info['error_type'],
            'retryable': error_info['retryable'],
            'success': False
        }
    finally:
        # Clean up uploaded file
        resource_manager.cleanup_file(file_path, ignore_errors=True)


@app.route('/api/upload', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)  # 10 requests per minute
def upload_file():
    """Handle file upload and processing."""
    try:
        if 'file' not in request.files:
            logger.warning("Upload attempt with no file")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.warning("Upload attempt with empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            logger.warning("Upload attempt with unsupported file type", filename=file.filename)
            return jsonify({'error': 'File type not supported'}), 400
        
        # Get API keys from config
        openai_api_key = Config.OPENAI_API_KEY
        deepseek_api_key = Config.DEEPSEEK_API_KEY
        
        # Validate configuration
        is_valid, error_msg = Config.validate()
        if not is_valid:
            logger.error("Configuration validation failed", error=error_msg)
            return jsonify({'error': error_msg}), 500
        
        # Save uploaded file
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        logger.info("File uploaded", filename=filename, file_path=file_path, size=os.path.getsize(file_path))
        
        # Pre-processing guardrails check
        if Config.ENABLE_GUARDRAILS:
            try:
                from utils.guardrails import Guardrails
                guardrails = Guardrails()
                is_allowed, violations = guardrails.validate_before_processing(file_path, filename)
                if not is_allowed:
                    logger.warning("File rejected by guardrails", violations=violations)
                    # Clean up file
                    try:
                        os.remove(file_path)
                    except:
                        pass
                    return jsonify({
                        'error': 'File rejected by security guardrails',
                        'violations': violations
                    }), 400
            except Exception as e:
                logger.error("Guardrails pre-check error", error=str(e))
                # Continue processing if guardrails check fails
        
        # Check if async processing is requested
        use_async = request.args.get('async', 'false').lower() == 'true'
        
        if use_async:
            # Submit as background task
            task_id = task_manager.submit_task(
                process_file_task,
                file_path=file_path,
                openai_api_key=openai_api_key,
                deepseek_api_key=deepseek_api_key,
                output_dir=str(project_root / 'output')
            )
            
            logger.info("Task submitted for async processing", task_id=task_id, filename=filename)
            return jsonify({
                'task_id': task_id,
                'status': 'pending',
                'message': 'File processing started in background'
            }), 202
        
        else:
            # Synchronous processing
            result = process_file_task(file_path, openai_api_key, deepseek_api_key, str(project_root / 'output'))
            
            if 'error' in result:
                return jsonify(result), 500
            
            return jsonify(result), 200
        
    except Exception as e:
        error_info = handle_api_error(e)
        logger.exception("Upload endpoint error", error=str(e))
        return jsonify({
            'error': str(e),
            'error_type': error_info['error_type']
        }), 500


@app.route('/api/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """Get status of a background task."""
    try:
        task = task_manager.get_task_status(task_id)
        
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        response = {
            'task_id': task_id,
            'status': task['status'],
            'progress': task.get('progress', 0.0),
            'created_at': task.get('created_at'),
        }
        
        if task['status'] == TaskStatus.COMPLETED:
            response['result'] = task.get('result')
        elif task['status'] == TaskStatus.FAILED:
            response['error'] = task.get('error')
        
        if task.get('started_at'):
            response['started_at'] = task['started_at']
        if task.get('completed_at'):
            response['completed_at'] = task['completed_at']
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error("Error getting task status", task_id=task_id, error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint with detailed status."""
    try:
        # Get system status
        task_stats = {
            'total_tasks': len(task_manager.tasks),
            'pending': sum(1 for t in task_manager.tasks.values() if t['status'] == TaskStatus.PENDING),
            'processing': sum(1 for t in task_manager.tasks.values() if t['status'] == TaskStatus.PROCESSING),
            'completed': sum(1 for t in task_manager.tasks.values() if t['status'] == TaskStatus.COMPLETED),
            'failed': sum(1 for t in task_manager.tasks.values() if t['status'] == TaskStatus.FAILED)
        }
        
        resource_stats = {
            'tracked_files': resource_manager.get_tracked_count()
        }
        
        # Validate configuration
        config_valid, config_error = Config.validate()
        
        return jsonify({
            'status': 'healthy' if config_valid else 'degraded',
            'service': 'data_labeling_system',
            'config_valid': config_valid,
            'config_error': config_error if not config_valid else None,
            'tasks': task_stats,
            'resources': resource_stats,
            'workers': len(task_manager.workers)
        }), 200
        
    except Exception as e:
        logger.error("Health check error", error=str(e))
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics."""
    try:
        # Get learning insights if available
        learning_insights = None
        try:
            from orchestrator_agentic import AgenticOrchestrator
            from config import Config
            temp_orchestrator = AgenticOrchestrator(
                deepseek_api_key=Config.DEEPSEEK_API_KEY,
                openai_api_key=Config.OPENAI_API_KEY
            )
            learning_insights = temp_orchestrator.learning_analyzer.get_learning_insights()
        except Exception as e:
            logger.debug("Could not get learning insights", error=str(e))
        
        stats = {
            'tasks': {
                'total': len(task_manager.tasks),
                'by_status': {
                    status: sum(1 for t in task_manager.tasks.values() if t['status'] == status)
                    for status in [TaskStatus.PENDING, TaskStatus.PROCESSING, TaskStatus.COMPLETED, TaskStatus.FAILED]
                }
            },
            'resources': {
                'tracked_files': resource_manager.get_tracked_count()
            }
        }
        
        if learning_insights:
            # Safely extract learning insights with defaults
            performance = learning_insights.get('performance', {})
            stats['learning'] = {
                'total_experiences': learning_insights.get('total_learning_examples', 0),
                'avg_quality': performance.get('avg_quality', 0.0),
                'success_rate': performance.get('success_rate', 0.0),
                'quality_trend': performance.get('quality_trend', 'stable'),
                'recommendations': learning_insights.get('recommendations', [])[:3]  # Top 3 recommendations
            }
        
        return jsonify(stats), 200
    except Exception as e:
        logger.error("Stats endpoint error", error=str(e))
        return jsonify({'error': str(e)}), 500


@app.route('/api/learning', methods=['GET'])
def get_learning_insights():
    """Get learning insights and recommendations."""
    try:
        from orchestrator_agentic import AgenticOrchestrator
        from config import Config
        
        orchestrator = AgenticOrchestrator(
            deepseek_api_key=Config.DEEPSEEK_API_KEY,
            openai_api_key=Config.OPENAI_API_KEY
        )
        
        insights = orchestrator.learning_analyzer.get_learning_insights()
        return jsonify(insights), 200
    except Exception as e:
        logger.error("Learning insights endpoint error", error=str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/status', methods=['GET'])
def get_cache_status():
    """Get cache status and statistics."""
    try:
        from orchestrator_agentic import AgenticOrchestrator
        from config import Config
        
        orchestrator = AgenticOrchestrator(
            deepseek_api_key=Config.DEEPSEEK_API_KEY,
            openai_api_key=Config.OPENAI_API_KEY
        )
        
        cache_status = {
            'enabled': Config.ENABLE_CACHING,
            'memory_cache_enabled': Config.ENABLE_MEMORY_CACHE,
            'db_cache_enabled': Config.ENABLE_DB_CACHE,
            'memory_cache_size': Config.MEMORY_CACHE_SIZE,
            'memory_cache_ttl': Config.MEMORY_CACHE_TTL,
            'cache_initialized': orchestrator.result_cache is not None
        }
        
        if orchestrator.result_cache:
            try:
                cache_stats = orchestrator.result_cache.get_cache_stats()
                cache_status['statistics'] = cache_stats
            except Exception as e:
                logger.warning("Failed to get cache statistics", error=str(e))
                cache_status['statistics'] = None
                cache_status['statistics_error'] = str(e)
        else:
            cache_status['statistics'] = None
            cache_status['message'] = 'Cache is not initialized'
        
        return jsonify(cache_status), 200
    except Exception as e:
        logger.error("Cache status endpoint error", error=str(e))
        return jsonify({
            'error': str(e),
            'enabled': Config.ENABLE_CACHING if hasattr(Config, 'ENABLE_CACHING') else None
        }), 500

if __name__ == '__main__':
    # Validate configuration before starting
    is_valid, error_msg = Config.validate()
    if not is_valid:
        logger.critical("Configuration validation failed", error=error_msg)
        print(f"ERROR: {error_msg}")
        print("\nPlease set your API keys using one of these methods:")
        print("1. Environment variable: export OPENAI_API_KEY='your-key'")
        print("2. Edit config.py and set OPENAI_API_KEY directly")
        exit(1)
    
    # Create necessary directories (using absolute paths)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(str(project_root / 'output'), exist_ok=True)
    os.makedirs(str(project_root / 'logs'), exist_ok=True)
    os.makedirs(str(project_root / 'logs' / 'agents'), exist_ok=True)
    
    # Start background task manager
    task_manager.start()
    
    logger.info("Configuration validated successfully")
    logger.info("Starting Flask server", host='0.0.0.0', port=5000)
    
    # Enable debug mode by default to see detailed error messages
    # In production, set debug=False and use a proper WSGI server
    debug_mode = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000, use_reloader=False)

