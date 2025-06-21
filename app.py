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