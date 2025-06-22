from flask import Flask, request, jsonify, render_template_string
from PyPDF2 import PdfReader
from langchain.vectorstores.cassandra import Cassandra
from langchain.indexes.vectorstore import VectorStoreIndexWrapper
from langchain.llms import OpenAI
from langchain.embeddings import OpenAIEmbeddings
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
        llm = OpenAI(openai_api_key = OPENAI_API_KEY)
        embedding = OpenAIEmbeddings(openai_api_key = OPENAI_API_KEY)
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

    try:
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
        
        vector_store.add_texts(texts)
        logger.info(f"Processed and stored {len(texts)}.")
        return len(texts)

    except Exception as e:
        logger.error(f"Error processing text: {str(e)}.")
        return None

@app.route('/')
def index():
    return

@app.route('/upload', methods = ['POST'])
def upload_pdf():
   

        

