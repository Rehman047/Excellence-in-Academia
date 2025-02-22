import os
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
from utils.text_processor import TextProcessor
from utils.question_generator import QuestionGenerator
import json

app = Flask(__name__)
text_processor = TextProcessor()
question_generator = QuestionGenerator()
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'pdf', 'pptx', 'docx', 'txt'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Store the file path in session for processing
            session['current_file'] = filepath
            return jsonify({
                'success': True,
                'message': 'File uploaded successfully',
                'filename': filename
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/generate-questions', methods=['POST'])
def generate_questions_route():
    if 'current_file' not in session:
        return jsonify({'error': 'No file uploaded'}), 400
    
    filepath = session['current_file']
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    try:
        # Get number of questions from request
        data = request.get_json()
        num_questions = data.get('num_questions', 10)  # Default to 10 if not specified
        
        # Validate number of questions
        num_questions = max(5, min(20, num_questions))  # Ensure between 5 and 20
        
        # Extract text from the uploaded file
        extracted_text = text_processor.extract_text(filepath)
        processed_text = text_processor.preprocess_text(extracted_text)
        
        # Generate questions from the processed text
        questions = question_generator.generate_questions(processed_text, num_questions)
        
        # Store questions in session for later use
        session['current_questions'] = questions
        
        return jsonify({
            'success': True,
            'message': 'Questions generated successfully',
            'questions': questions
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/results')
def results():
    return render_template('results.html')

if __name__ == '__main__':
    app.run(debug=True, port=5002)
