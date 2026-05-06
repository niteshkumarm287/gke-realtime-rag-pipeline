import json
import uuid
from datetime import datetime, timezone
from google.cloud import storage


class GCSLogWriter:
    def __init__(self, bucket_name: str, prefix: str = "raw"):
        self.bucket_name = bucket_name
        self.prefix = prefix
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)

    def write(self, log_entry: dict):
        """Write a single log entry as a JSON file."""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry["timestamp"] = timestamp

        blob_name = (
            f"{self.prefix}/"
            f"{datetime.utcnow().strftime('%Y/%m/%d/%H')}/"
            f"{uuid.uuid4()}.json"
        )

        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(
            json.dumps(log_entry),
            content_type="application/json"
        )

        return blob_name