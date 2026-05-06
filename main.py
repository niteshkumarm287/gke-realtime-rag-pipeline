import functions_framework
import vertexai
from vertexai.preview import rag
from google.cloud import secretmanager, storage
import os
import json
import traceback

PROJECT_ID = os.environ["GCP_PROJECT"]
REGION = os.environ["REGION"]

DEBUG = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}
SKIP_RAG = os.getenv("DEBUG_SKIP_RAG_IMPORT", "false").lower() in {"1", "true", "yes"}


# -----------------------------
# Helpers
# -----------------------------
def log(msg):
    print(msg)


def debug(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")


def get_corpus_name():
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/rag-corpus-name/versions/latest"
    response = client.access_secret_version(request={"name": name})
    corpus = response.payload.data.decode("utf-8").strip()
    debug(f"Resolved corpus: {corpus}")
    return corpus


def extract_text(content: str) -> str:
    """
    Convert JSON → meaningful text
    """
    try:
        parsed = json.loads(content)

        if isinstance(parsed, dict):
            return " ".join([str(v) for v in parsed.values()])

        if isinstance(parsed, list):
            return " ".join([str(item) for item in parsed])

        return str(parsed)

    except Exception:
        debug("Content is not valid JSON, using raw text")
        return content


def upload_txt(bucket, object_name, text):
    storage_client = storage.Client()
    txt_name = object_name.replace(".json", ".txt")

    blob = storage_client.bucket(bucket).blob(txt_name)
    blob.upload_from_string(text, content_type="text/plain")

    return f"gs://{bucket}/{txt_name}"


# -----------------------------
# Main Function
# -----------------------------
@functions_framework.cloud_event
def handle_gcs_event(cloud_event):
    try:
        data = cloud_event.data
        bucket = data["bucket"]
        object_name = data["name"]

        debug(f"Event: {json.dumps(data)}")

        # ✅ Filter early (VERY IMPORTANT)
        if not object_name.startswith("raw/") or not object_name.endswith(".json"):
            log(f"Skipping: {object_name}")
            return

        log(f"Processing: gs://{bucket}/{object_name}")

        # -----------------------------
        # Download file
        # -----------------------------
        storage_client = storage.Client()
        blob = storage_client.bucket(bucket).blob(object_name)

        content = blob.download_as_text()
        debug(f"Downloaded {len(content)} chars")

        # -----------------------------
        # Convert → clean text
        # -----------------------------
        text_content = extract_text(content)

        if not text_content.strip():
            log("Empty content after parsing, skipping")
            return

        debug(f"Text preview: {text_content[:200]}")

        # -----------------------------
        # Upload .txt version
        # -----------------------------
        txt_uri = upload_txt(bucket, object_name, text_content)
        log(f"Prepared text file: {txt_uri}")

        if SKIP_RAG:
            log(f"[DEBUG] Skipping RAG import")
            return

        # -----------------------------
        # Vertex AI RAG Import
        # -----------------------------
        vertexai.init(project=PROJECT_ID, location=REGION)

        corpus_name = get_corpus_name()

        log(f"Importing into RAG...")

        response = rag.import_files(
            corpus_name=corpus_name,
            paths=[txt_uri],
            transformation_config=rag.TransformationConfig(
                chunking_config=rag.ChunkingConfig(
                    chunk_size=512,
                    chunk_overlap=50
                )
            )
        )

        debug(f"RAG response: {response}")

        log(f"✅ SUCCESS: Imported {txt_uri}")

    except Exception as e:
        log("❌ ERROR during processing")
        log(str(e))
        log(traceback.format_exc())
        raise