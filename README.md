# AI Document Q&A App

This is a comprehensive AI-powered document and multimedia Question & Answering web application. It allows users to upload documents and interact with an AI chatbot to ask questions about the uploaded content using semantic search and retrieval-augmented generation (RAG).

## Features

- **Document Upload**: Securely upload and manage documents.
- **AI Chatbot**: Conversational interface with streaming responses.
- **Semantic Search**: FAISS integration for efficient and accurate document retrieval.
- **Multimedia Support**: Integration with Whisper for audio/video transcription.
- **User Authentication**: Secure multi-user authentication with JWT.

## Tech Stack

- **Backend**: FastAPI, Python
- **Frontend**: React, JavaScript/TypeScript
- **Database**: PostgreSQL
- **LLM/Embeddings**: Ollama (Local AI models)
- **Vector Search**: FAISS
- **Containerization**: Docker & Docker Compose

## Getting Started

### Prerequisites

- Docker and Docker Compose
- (Optional) Local installation of Python and Node.js for direct development without Docker.

### Running with Docker

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ProjectAced
   ```

2. Set up environment variables:
   Copy `.env.example` to `.env` and adjust the values if necessary.
   ```bash
   cp .env.example .env
   ```

3. Start the application:
   ```bash
   docker-compose up --build
   ```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Ollama**: http://localhost:11434

## Project Structure

- `/backend`: FastAPI application, FAISS indexing logic, and database schemas.
- `/frontend`: React frontend application.
- `docker-compose.yml`: Docker configuration for the full stack.
