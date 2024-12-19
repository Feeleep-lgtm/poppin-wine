import os
import shutil
import logging
from django.core.management.base import BaseCommand
from asgiref.sync import sync_to_async
from thepopwinegdrives.models import Book, ScrapedContent
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Determine if we are in PRODUCTION or development
CHROMA_PATH = os.getenv("CHROMA_PERSISTENT_PATH", "chroma")

logger.info(f"Chroma path is: {CHROMA_PATH}")

class Command(BaseCommand):
    help = 'Create and populate the Chroma database'

    def handle(self, *args, **kwargs):
        try:
            self.generate_data_store()
        except Exception as e:
            logger.error("An error occurred while generating the data store", exc_info=True)
            self.stdout.write(self.style.ERROR(f"Failed to generate the data store: {e}"))

    def generate_data_store(self):
        try:
            documents = self.load_documents()
            chunks = self.split_text(documents)
            self.save_to_chroma(chunks)
        except Exception as e:
            logger.error("An error occurred during the data store generation process", exc_info=True)
            raise

    def load_documents(self):
        documents = []

        try:
            # Load documents from Book and ScrapedContent models synchronously
            books = Book.objects.all()
            for book in books:
                documents.append({
                    "page_content": book.content,
                    "metadata": {"source": book.title}
                })

            scraped_contents = ScrapedContent.objects.all()
            for content in scraped_contents:
                documents.append({
                    "page_content": content.content,
                    "metadata": {"source": content.title}
                })

            logger.info(f"Loaded {len(documents)} documents from database.")
        except Exception as e:
            logger.error("An error occurred while loading documents", exc_info=True)
            raise

        return documents

    def split_text(self, documents):
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=300,
                chunk_overlap=100,
                length_function=len,
                add_start_index=True,
            )
            chunks = []
            for doc in documents:
                doc_chunks = text_splitter.split_text(doc["page_content"])
                for chunk in doc_chunks:
                    chunks.append({
                        "page_content": chunk,
                        "metadata": doc["metadata"]
                    })

            logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks.")
        except Exception as e:
            logger.error("An error occurred while splitting text", exc_info=True)
            raise

        return chunks

    def save_to_chroma(self, chunks):
        try:
            if os.path.exists(CHROMA_PATH):
                shutil.rmtree(CHROMA_PATH)

            texts = [chunk["page_content"] for chunk in chunks]
            metadatas = [chunk["metadata"] for chunk in chunks]

            embeddings = OpenAIEmbeddings()
            db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
            db.add_texts(texts=texts, metadatas=metadatas)
            db.persist()

            logger.info(f"Saved {len(chunks)} chunks to {CHROMA_PATH}.")
        except Exception as e:
            logger.error("An error occurred while saving data to Chroma", exc_info=True)
            raise
