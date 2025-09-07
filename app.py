"""
Flask Application - ESG PDF Semantic Search Viewer
Main application file with routes and configuration
"""

import os
import json
from flask import Flask, request, render_template, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Import our PDF extraction module
from pdf_extractor import extract_esg_pdf_sentences
from semantic_search.search import SemanticSearchESG

# Initialize semantic search model
print("🤖 Initializing SemanticSearchESG model...")
semantic_search = SemanticSearchESG(similarity_threshold=0.4)

# Flask application setup
app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


def allowed_file(filename):
    """
    Check if the uploaded file is allowed
    
    Args:
        filename (str): Name of the uploaded file
        
    Returns:
        bool: True if file extension is allowed
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    """
    Main page route - serves the PDF upload interface
    
    Returns:
        str: Rendered HTML template
    """
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_pdf():
    """
    Handle PDF file upload and process for ESG content
    
    Returns:
        json: ESG analysis results or error message
    """
    # Validate file upload
    pdf_file = request.files.get("pdf_file")
    if not pdf_file:
        print("🚫 No file uploaded")
        return jsonify({"error": "No file uploaded"}), 400
    
    if pdf_file.filename == '':
        print("🚫 Empty filename")
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(pdf_file.filename):
        print("🚫 Invalid file type")
        return jsonify({"error": "Only PDF files are allowed"}), 400

    try:
        # Save uploaded file
        filename = secure_filename(pdf_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        pdf_file.save(filepath)
        print(f"📄 Saved uploaded PDF to {filepath}")

        # Process PDF for text extraction
        extracted_data = extract_esg_pdf_sentences(filepath)
        
        if not extracted_data:
            print("❌ No text found even after processing.")
            return jsonify({"error": "No text found in the PDF"}), 400

        # Run ESG semantic search
        print(f"🔬 Running ESG semantic search on {len(extracted_data)} chunks...")
        esg_results = semantic_search.run_semantic_search(extracted_data)
        print(f"🎯 Found {len(esg_results)} ESG-related sentences.")

        return jsonify(esg_results)
        
    except Exception as e:
        print(f"❌ Error processing PDF: {str(e)}")
        return jsonify({"error": f"Error processing PDF: {str(e)}"}), 500


@app.route('/uploads/<path:filename>')
def serve_uploaded_pdf(filename):
    """
    Serve uploaded PDF files
    
    Args:
        filename (str): Name of the PDF file to serve
        
    Returns:
        file: PDF file response
    """
    print(f"📦 Serving uploaded PDF: {filename}")
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return jsonify({"error": "File not found"}), 404


@app.route("/pdf_viewer")
def pdf_viewer():
    """
    PDF viewer route - displays PDF with highlighting capability
    
    Returns:
        str: Rendered PDF viewer template or error message
    """
    pdf_file = request.args.get('file')
    highlight_json = request.args.get('highlight')

    print(f"👀 PDF viewer requested for file: {pdf_file}")
    
    if highlight_json:
        print(f"🔦 Highlight info received: {highlight_json}")
        try:
            highlight_data = json.loads(highlight_json)
            print(f"🔍 Parsed highlight data: {highlight_data}")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse highlight JSON: {e}")
    else:
        print("ℹ️ No highlight info received")

    if not pdf_file:
        print("⚠️ No PDF file specified in viewer request")
        return "No PDF file specified", 400

    # Verify file exists
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file)
    if not os.path.exists(filepath):
        print(f"❌ PDF file does not exist: {filepath}")
        return "PDF file not found", 404

    return render_template("viewer.html", pdf_url=pdf_file, highlight=highlight_json)


@app.route("/debug_test")
def debug_test():
    """
    Debug route for testing purposes
    
    Returns:
        str: Debug template
    """
    pdf_file = request.args.get('file')
    highlight_json = request.args.get('highlight')
    print(f"🔧 Debug test requested - file: {pdf_file}, highlight: {highlight_json}")
    return render_template("debug_test.html")


@app.route("/health")
def health_check():
    """
    Health check endpoint
    
    Returns:
        json: Application status
    """
    return jsonify({
        "status": "healthy",
        "upload_folder": app.config['UPLOAD_FOLDER'],
        "max_file_size": app.config['MAX_CONTENT_LENGTH']
    })


@app.errorhandler(413)
def too_large(e):
    """
    Handle file too large error
    
    Returns:
        json: Error message for oversized files
    """
    return jsonify({"error": "File too large. Maximum size is 50MB."}), 413


@app.errorhandler(404)
def not_found(e):
    """
    Handle 404 errors
    
    Returns:
        json: 404 error message
    """
    return jsonify({"error": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    """
    Handle internal server errors
    
    Returns:
        json: 500 error message
    """
    return jsonify({"error": "Internal server error"}), 500

@app.route("/test-sharp-rendering.html")
def test_sharp_rendering():
    return render_template("test-sharp-rendering.html")

@app.route("/sharp-test.html")
def sharp_test():
    return render_template("sharp-test.html")

if __name__ == "__main__":
    print("🚀 Starting ESG PDF Semantic Search Application...")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📊 Max file size: {MAX_CONTENT_LENGTH / (1024*1024):.0f}MB")
    
    app.run(
        debug=True, 
        host="0.0.0.0", 
        port=8080,
        threaded=True
    )