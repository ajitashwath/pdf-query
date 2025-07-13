from flask import Flask, request, jsonify, render_template
from PyPDF2 import PdfReader
from langchain_community.vectorstores import Cassandra
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain_community.llms import OpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import cassio
import os
import logging

load_dotenv()

logging.basicConfig(level = logging.INFO, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 10
app.config['UPLOAD_FOLDER'] = 'uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok = True)

ASTRA_DB_APPLICATION_TOKEN = os.getenv('ASTRA_DB_APPLICATION_TOKEN')
ASTRA_DB_ID = os.getenv('ASTRA_DB_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

vector_store = None
vector_index = None
llm = None
embedding = None

def initialize_components():
    global vector_store, vector_index, llm, embedding

    try:
        if not all([ASTRA_DB_APPLICATION_TOKEN, ASTRA_DB_ID, OPENAI_API_KEY]):
            logger.error("Missing environment variables.")
            return False
        cassio.init(token = ASTRA_DB_APPLICATION_TOKEN, database_id = ASTRA_DB_ID)
        logger.info("Astro DB Connection Initialized.")
        llm = OpenAI()
        embedding = OpenAIEmbeddings()
        logger.info("OpenAI Components Initialized.")

        vector_store = Cassandra(
            embedding = embedding,
            table_name = "pdf_query",
            session = None,
            keyspace = None,
        )

        vector_index = VectorStoreIndexWrapper(vectorstore = vector_store)
        logger.info("Vector Space Initialized.")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize components: {str(e)}")
        return False


def extract_text_from_pdf(pdf_path):
    try:
        reader = PdfReader(pdf_path)
        raw_text = ''
        for page in reader.pages:
            content = page.extract_text()
            if content:
                raw_text += content
        
        if not raw_text.strip():
            logger.warning("No text extracted from PDF.")
            return None
        
        logger.info(f"Extracted {len(raw_text)} characters.")
        return raw_text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return None
    
def process_and_store_text(text):
    global vector_store
    if vector_store is None:
        if not initialize_components():
            logger.error("Failed to initialize vector_store.")
            return None
    # Now safe to use vector_store
    text_splitter = CharacterTextSplitter(
        separator = "\n",
        chunk_size = 800,
        chunk_overlap = 200,
        length_function = len,
    )

    texts = text_splitter.split_text(text)
    if not texts:
        logger.warning("No text chunks created.")
        return None
    
    if vector_store is None:
        logger.error("vector_store is not initialized after attempted initialization.")
        return None
    vector_store.add_texts(texts)
    logger.info(f"Processed and stored {len(texts)}.")
    return len(texts)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods = ['POST'])
def upload_pdf():
    try:
        if 'pdf' not in request.files:
            return jsonify({'success': False, 'error': 'No PDF file provided'})
        file = request.files['pdf']
        if not file or not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not isinstance(file.filename, str) or not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Please upload a PDF file'})

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        logger.info(f"File saved: {filename}")

        text = extract_text_from_pdf(filepath)
        if not text:
            os.remove(filepath)
            return jsonify({'success': False, 'error': 'Failed to extract text from PDF. Please ensure the PDF contains readable text.'})

        chunk_count = process_and_store_text(text)
        if chunk_count is None:
            os.remove(filepath)
            return jsonify({'success': False, 'error': 'Failed to process and store text'})

        os.remove(filepath)
        logger.info(f"Successfully processed PDF: {filename}")
        return jsonify({
            'success': True,
            'message': f'PDF Processed successfully! Created {chunk_count} text chunks. You can ask questions now.'
        })

    except Exception as e:
        logger.error(f"Error in upload_pdf: {str(e)}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'})

@app.route('/query', methods = ['POST'])
def query_pdf():
    try:
        global vector_store, vector_index
        if vector_store is None or vector_index is None:
            if not initialize_components():
                return jsonify({'success': False, 'error': 'System not initialized. Please restart the application.'})
        if vector_index is None or vector_store is None:
            return jsonify({'success': False, 'error': 'System not initialized. Please restart the application.'})
        
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'success': False, 'error': 'No question provided'})
        
        question = data['question'].strip()
        if not question:
            return jsonify({'success': False, 'error': 'Question cannot be empty'})
        
        logger.info(f"Processing query: {question[:100]}...")
        
        # Get answer from vector index
        answer = vector_index.query(question, llm=llm).strip()
        
        # Get relevant documents with scores
        relevant_docs = vector_store.similarity_search_with_score(question, k=4)
        
        # Format relevant documents
        docs_data = []
        for doc, score in relevant_docs:
            docs_data.append({
                'score': float(score),
                'content': doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
            })
        
        logger.info(f"Query processed successfully, found {len(docs_data)} relevant documents")
        
        return jsonify({
            'success': True,
            'answer': answer,
            'relevant_docs': docs_data
        })
        
    except Exception as e:
        logger.error(f"Error in query_pdf: {str(e)}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'})

@app.route('/health')
def health_check():
    status = {
        'status': 'healthy',
        'components': {
            'vector_store': vector_store is not None,
            'llm': llm is not None,
            'embedding': embedding is not None
        }
    }
    return jsonify(status)

@app.errorhandler(413)
def too_large(e):
    return jsonify({'success': False, 'error': 'File too large. Maximum size is 16MB.'}), 413

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Interval server error: {str(e)}")
    return jsonify({'success': False, 'error': 'File too large. Maximum size is 16 MB.'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(debug = debug, host = '0.0.0.0', port = port)