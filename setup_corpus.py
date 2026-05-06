import os
import vertexai
from vertexai.preview import rag

PROJECT_ID = os.getenv("PROJECT_ID")
REGION = os.getenv("REGION")

vertexai.init(project=PROJECT_ID, location=REGION)

corpus = rag.create_corpus(
    display_name="rag-log-corpus",
    description="Real-time app log corpus"
)

print(f"Corpus created: {corpus.name}")