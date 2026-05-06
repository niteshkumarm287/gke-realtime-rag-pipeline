# GKE Real-time RAG Pipeline

This project demonstrates an end-to-end event-driven RAG (Retrieval-Augmented Generation) pipeline on Google Cloud Platform (GCP). It uses GKE, GCS, Eventarc, Cloud Functions, and Vertex AI to ingest logs in real-time, index them into a RAG corpus, and enable grounded responses via a FastAPI service.

## Architecture

The pipeline consists of the following components:

1.  **FastAPI Log Service (`app.py`):**
    *   A FastAPI application running on GKE.
    *   Exposes a `/log` endpoint to receive log messages.
    *   Writes the logs as JSON files to a GCS bucket in a `raw/` directory.

2.  **GCS Bucket:**
    *   Stores the raw log files.
    *   Triggers a Cloud Function when a new log file is uploaded.

3.  **Cloud Function (`main.py`):**
    *   Triggered by new files in the GCS bucket.
    *   Processes the JSON log file, extracts the text content, and creates a `.txt` file.
    *   Imports the `.txt` file into a Vertex AI RAG corpus using `rag.import_files`.

4.  **Vertex AI RAG Corpus:**
    *   Stores the indexed log data.
    *   Can be used to provide grounded responses from a large language model (e.g., Gemini).

## Project Structure

```
.
├── app.py              # FastAPI log service
├── main.py             # Cloud Function for RAG import
├── deployment.yaml     # Kubernetes deployment for the FastAPI service
├── Dockerfile          # For containerizing the FastAPI service
├── requirements.txt    # Python dependencies
├── function/           # Directory for Cloud Function source code
├── ...
└── README.md           # This file
```

## Getting Started

### Prerequisites

*   A Google Cloud Platform project.
*   gcloud CLI authenticated to your project.
*   Docker.
*   A GCS bucket.
*   A Vertex AI RAG corpus.
*   A secret in Secret Manager named `rag-corpus-name` containing the full name of your RAG corpus.

### Setup and Deployment

1.  **Deploy the FastAPI service to GKE:**
    *   Update the `BUCKET_NAME` environment variable in `deployment.yaml` to your GCS bucket name.
    *   Build and push the Docker image:
        ```bash
        docker build -t gcr.io/YOUR_PROJECT_ID/gke-rag-fastapi .
        docker push gcr.io/YOUR_PROJECT_ID/gke-rag-fastapi
        ```
    *   Deploy to GKE:
        ```bash
        gcloud container clusters create ...
        kubectl apply -f deployment.yaml
        ```

2.  **Deploy the Cloud Function:**
    *   Deploy the function from the `main.py` file, triggered by GCS events on the `raw/` directory of your bucket.
    *   Set the required environment variables (`GCP_PROJECT`, `REGION`).

### Usage

1.  **Send a log to the FastAPI service:**
    ```bash
    curl -X POST http://YOUR_FASTAPI_SERVICE_IP/log \
    -H "Content-Type: application/json" \
    -d '{"message": "This is a test log message."}'
    ```

2.  **Check the GCS bucket:**
    *   A new JSON file should appear in the `raw/` directory.
    *   A new `.txt` file should be created in the bucket root.

3.  **Check the RAG corpus:**
    *   The new log message should be indexed and available for retrieval in your Vertex AI RAG corpus.