# PDF Query System

A Flask-based web application that allows users to upload PDF documents and ask questions about their content using AI-powered natural language processing. The system uses OpenAI's language models and embeddings with Cassandra vector database for efficient document retrieval and question answering.

## Features

- **PDF Upload**: Drag-and-drop or click-to-upload PDF files (up to 16MB)
- **Text Extraction**: Automatic text extraction from PDF documents
- **Vector Storage**: Efficient text chunking and vector storage using Cassandra
- **AI-Powered Q&A**: Natural language question answering using OpenAI's GPT models
- **Relevance Scoring**: Shows relevant document excerpts with similarity scores
- **Responsive UI**: Clean, modern web interface with real-time feedback
- **Docker Support**: Containerized deployment for easy scaling

## Technology Stack
- **Backend**: Python, Flask, Gunicorn
- **AI/ML**: OpenAI GPT models, LangChain, OpenAI Embeddings
- **Database**: Cassandra (via DataStax Astra DB)
- **PDF Processing**: PyPDF2
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Deployment**: Docker, Docker Compose

## Prerequisites

Before running the application, you need to set up the following services:

### 1. OpenAI API Key
- Sign up at [OpenAI](https://platform.openai.com/)
- Generate an API key from the dashboard
- Ensure you have sufficient credits/quota

### 2. DataStax Astra DB (Cassandra)
- Sign up at [DataStax Astra](https://astra.datastax.com/)
- Create a new database
- Generate an application token
- Note down your Database ID

### 3. System Requirements
- Docker and Docker Compose installed
- At least 2GB RAM available
- 1GB free disk space

## Installation and Setup

### 1. Clone the Repository
```bash
git clone https://github.com/ajitashwath/pdf-query.git
cd pdf-query
```

### 2. Environment Configuration
Create a `.env` file in the project root with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Astra DB Configuration
ASTRA_DB_APPLICATION_TOKEN=your_astra_db_token_here
ASTRA_DB_ID=your_astra_db_id_here

# Flask Configuration (Optional)
FLASK_ENV=production
PORT=5000
```

**Important**: Never commit your `.env` file to version control. It's already included in `.gitignore`.

### 3. Build and Run with Docker Compose

```bash
# Build and start the application
docker compose up --build

# Or run in detached mode
docker compose up --build -d
```

### 4. Access the Application
Open your browser and navigate to: `http://localhost:8000`

## Usage Guide

### 1. Upload a PDF Document
- Click on the upload area or drag and drop a PDF file
- Maximum file size: 16MB
- The system will extract text and create vector embeddings
- Wait for the "PDF processed successfully" message

### 2. Ask Questions
- Type your question in the input field
- Click "Ask Question" to get AI-powered answers
- The system will show:
  - **Answer**: AI-generated response based on the document
  - **Relevant Excerpts**: Source text with relevance scores

### 3. Example Questions
- "What is the main topic of this document?"
- "Summarize the key findings"
- "What are the conclusions?"
- "Extract all the important dates mentioned"

## API Endpoints

The application provides the following REST API endpoints:

### POST `/upload`
Upload and process a PDF document.

**Request**: Multipart form data with `pdf` file
**Response**: 
```json
{
  "success": true,
  "message": "PDF processed successfully! Created 15 text chunks."
}
```

### POST `/query`
Ask questions about the uploaded document.

**Request**: 
```json
{
  "question": "What is the main topic?"
}
```

**Response**:
```json
{
  "success": true,
  "answer": "The main topic is...",
  "relevant_docs": [
    {
      "score": 0.8542,
      "content": "Relevant text excerpt..."
    }
  ]
}
```

### GET `/health`
Health check endpoint for monitoring.

**Response**:
```json
{
  "status": "healthy",
  "components": {
    "vector_store": true,
    "llm": true,
    "embedding": true
  }
}
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models | Yes |
| `ASTRA_DB_APPLICATION_TOKEN` | DataStax Astra DB token | Yes |
| `ASTRA_DB_ID` | DataStax Astra DB database ID | Yes |
| `FLASK_ENV` | Flask environment (development/production) | No |
| `PORT` | Application port (default: 5000) | No |

### Application Settings

The application includes several configurable parameters in `app.py`:

- **File Upload Limit**: 16MB (configurable in `app.config['MAX_CONTENT_LENGTH']`)
- **Text Chunk Size**: 800 characters with 200 character overlap
- **Vector Search Results**: Top 4 most relevant chunks
- **Gunicorn Workers**: 2 workers with 120-second timeout

## Development

### Local Development Setup

1. **Create Virtual Environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set Environment Variables**:
```bash
export OPENAI_API_KEY="your_key_here"
export ASTRA_DB_APPLICATION_TOKEN="your_token_here"
export ASTRA_DB_ID="your_db_id_here"
export FLASK_ENV="development"
```

4. **Run the Application**:
```bash
python app.py
```

### Project Structure

```
pdf-query/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── compose.yaml          # Docker Compose configuration
├── .env                  # Environment variables (create this)
├── .gitignore           # Git ignore rules
├── .dockerignore        # Docker ignore rules
├── static/
│   ├── style.css        # CSS styles
│   └── script.js        # JavaScript functionality
├── templates/
│   └── index.html       # HTML template
└── uploads/             # Temporary file storage
```

## Deployment

### Production Deployment

1. **Environment Setup**:
   - Set `FLASK_ENV=production`
   - Use strong, unique API keys
   - Configure proper logging

2. **Resource Scaling**:
   - Adjust Gunicorn worker count based on CPU cores
   - Configure memory limits in Docker Compose
   - Set up load balancing for multiple instances

3. **Security Considerations**:
   - Use HTTPS in production
   - Implement rate limiting
   - Add authentication if needed
   - Regular security updates

### Cloud Deployment Options

The application can be deployed on various cloud platforms:

- **AWS**: ECS, EKS, or Elastic Beanstalk
- **Google Cloud**: Cloud Run, GKE, or App Engine
- **Azure**: Container Instances or App Service
- **DigitalOcean**: App Platform or Droplets

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:
- Check the troubleshooting section
- Review application logs
- Create an issue in the repository
- Check OpenAI and DataStax documentation
