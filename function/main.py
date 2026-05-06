import os
import logging
import functions_framework
import vertexai
from vertexai import rag

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ID  = os.environ["GCP_PROJECT"]
REGION      = os.environ.get("REGION", "asia-south1")
CORPUS_NAME = os.environ["CORPUS_NAME"]  # e.g. projects/game-d8160/locations/asia-south1/ragCorpora/6917529027641081856


@functions_framework.cloud_event
def handle_gcs_event(cloud_event):
    data        = cloud_event.data
    bucket      = data["bucket"]
    object_name = data["name"]

    if not object_name.startswith("raw/"):
        logger.info(f"Skipping non-raw file: {object_name}")
        return

    gcs_uri = f"gs://{bucket}/{object_name}"
    logger.info(f"Importing into RAG corpus: {gcs_uri}")

    vertexai.init(project=PROJECT_ID, location=REGION)

    response = rag.import_files(
        corpus_name=CORPUS_NAME,
        paths=[gcs_uri],
        transformation_config=rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(
                chunk_size=512,
                chunk_overlap=50,
            )
        ),
    )

    logger.info(f"Import complete — imported {response.imported_rag_files_count} file(s)")