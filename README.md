
 # UniGuide

UniGuide is a Retrieval-Augmented Generation (RAG) application built for universities.
It helps students find clear answers about university policies, course registration,
academic requirements, books, lectures, and other university resources.

Students can ask questions in natural language. UniGuide searches the university's
knowledge base and uses the most relevant information to generate an answer.

## Why I Built It

When I started university, I didn't always know how the university system worked, how to register for courses, or where to find the right information. There were also many misconceptions about university policies and requirements, which sometimes made things more confusing for me and my colleagues.

I built UniGuide to make this process simpler. The goal is to help students understand university policies, documents, courses, and other academic resources, and provide guidance throughout their university journey until graduation.

## How It Works

The application has two main workflows. First, an administrator uploads university
resources. UniGuide extracts the text, splits it into smaller chunks, and indexes
those chunks for semantic search.

When a student asks a question, UniGuide finds the most relevant chunks and sends
them as context to a generation model. This keeps the answer connected to the
university's own resources instead of relying only on the model's general knowledge.

## Technical Highlights

### Core RAG Pipeline

Administrators can upload files asynchronously with validation, streamed file
writing, and asset metadata storage. The application extracts and cleans the text,
splits it into chunks  using *(Langchain)*, stores the source metadata, and generates
embeddings for semantic search  .

When a student asks a question, UniGuide converts it into an embedding and searches
for the most relevant content. The retrieved context is added to the LLM prompt so
the answer is grounded in the university's own documents. Previous messages can
also be included when a student continues a conversation.

### Vector Database Options

The application supports two vector search backends:

- **Qdrant**: A dedicated vector database designed for semantic search.
- **PostgreSQL with pgvector**: Keeps vector search alongside the application's
	structured data.

The provider-based design makes the backend configurable without changing the main
RAG workflow.

### Data Modeling with PostgreSQL and SQLAlchemy

PostgreSQL stores projects, uploaded assets, processed data chunks, conversations,
and messages. SQLAlchemy provides the data access layer, while JSONB fields support
flexible document metadata. Database indexes are added to frequently queried fields
to keep lookups efficient as the amount of indexed content grows.

### Database Migrations

**Alembic** manages database schema changes under
`src/models/db_schemes/minirag/alembic/`. Migration scripts make database updates
repeatable across development and deployment environments without manually
recreating the tables.

### LLM and Prompt Provider System

Separate provider interfaces and factory classes allow generation and embedding
models to be configured independently. The project supports **OpenAI** and
**Cohere**, configurable model settings, and locale-based prompt templates. This
keeps provider-specific code separate from the API and makes it easier to add or
replace integrations.

### Monitoring and Observability

Prometheus middleware records request counts, status codes, and request latency. The
`/metrics` endpoint exposes these metrics for Prometheus, while Grafana can be used
to visualize service health and performance. Postgres Exporter provides database
metrics, and Node Exporter can be enabled for host-level metrics through the Docker
Compose `linux-host` profile.

### Docker Infrastructure

The backend runs in containers managed by **Docker Compose**. The setup includes
FastAPI, Nginx, PostgreSQL with pgvector, Qdrant, Prometheus, Grafana, Postgres
Exporter, and optional Node Exporter. Services share a backend network, named
volumes persist application and monitoring data, and health checks control service
startup. Nginx acts as the reverse proxy for the FastAPI service.


## System Overview

```text
								 Nginx Reverse Proxy
												|
												v
								 FastAPI Backend
												|
			 +----------------+----------------+
			 |                |                |
			 v                v                v
	RAG Pipeline    PostgreSQL        Prometheus
			 |          + pgvector             |
			 |                |                v
			 v                v             Grafana
		 Qdrant       Projects, Assets,
	 Vector Search  Chunks, Conversations
												|
												v
								 Student Questions
												|
												v
								 Grounded Answers
```

## Main RAG Flow

```text
University documents
	|
	v
Document extraction and cleaning
	|
	v
Text chunks and metadata
	|
	v
Embeddings and vector index
	|
	v
Student question -> Relevant context -> Generated answer
```

## Project Structure

The main application code is inside `src/`:

| Directory | Responsibility |
| --- | --- |
| `routes/` | Defines the HTTP endpoints and validates incoming requests. |
| `controller/` | Contains file processing, project management, data processing, and NLP logic. |
| `models/` | Provides database models, schemas, and data access operations. |
| `stores/llm/` | Contains LLM and embedding interfaces, providers, and prompt templates. |
| `stores/vectorDB/` | Contains vector database interfaces and Qdrant or pgvector providers. |
| `helpers/` | Loads application configuration and environment settings. |
| `utils/` | Contains shared utilities and Prometheus metrics. |

## API Endpoints

The API separates document preparation from search and answer generation. A typical
workflow uploads files, processes them into chunks, indexes the chunks, and then
uses search or answer generation endpoints.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/route1/` | Checks that the application is running and returns the application name. |
| `POST` | `/data/upload_files/{project_id}` | Uploads a document and stores its project asset metadata. |
| `POST` | `/data/process/{project_id}` | Extracts text, creates chunks, and stores processed content. |
| `POST` | `/nlp/index/push/{project_id}` | Generates embeddings and adds project chunks to the vector database. |
| `GET` | `/nlp/index/info/{project_id}` | Returns information about a project's vector collection. |
| `POST` | `/nlp/index/search/{project_id}` | Searches indexed content using a natural-language query. |
| `POST` | `/nlp/index/answer/{project_id}` | Retrieves relevant content and generates a grounded answer with conversation context. |
| `GET` | `/metrics` | Exposes Prometheus metrics for monitoring. |

## Requirements

- Python 3.13 for the Docker image
- Docker and Docker Compose
- API credentials for the selected generation and embedding providers

## Run with Docker Compose

Copy the example environment files and add your credentials:

```bash
cd docker
cp env/.env.app.example env/.env.app
cp env/.env.postgres.example env/.env.postgres
```

Then start the services:

```bash
docker compose up -d --build
```

The available services include the FastAPI application, PostgreSQL with pgvector,
Qdrant, Nginx, Prometheus, and Grafana.

## Run the API Locally

Install the Python dependencies:

```bash
cd src
pip install -r requirements.txt
```

Configure the required environment variables, then start the FastAPI server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Testing

A Postman collection is available at
[`src/assets/mini-rag-app.postman_collection.json`](src/assets/mini-rag-app.postman_collection.json).

The API includes endpoints for uploading and processing administrator content,
indexing project data, searching the vector database, and generating RAG answers
for student questions.

Made with love by Abdalaziz 