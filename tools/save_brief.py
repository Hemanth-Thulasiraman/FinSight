import os
import boto3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

def get_s3_client():
    """Create boto3 client pointing to Cloudflare R2."""
    return boto3.client(
        "s3",
        endpoint_url=f"https://{CLOUDFLARE_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name="auto"
    )

def save_brief(ticker: str, content: str) -> dict:
    """
    Save research brief to Cloudflare R2.
    Falls back to local file if R2 is unavailable.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"briefs/brief_{ticker}_{timestamp}.md"

    # Try R2 first
    if CLOUDFLARE_ACCOUNT_ID and AWS_ACCESS_KEY_ID:
        try:
            client = get_s3_client()
            client.put_object(
                Bucket=BUCKET_NAME,
                Key=file_name,
                Body=content.encode("utf-8"),
                ContentType="text/markdown"
            )
            s3_path = f"r2://{BUCKET_NAME}/{file_name}"
            return {
                "error": False,
                "file_path": s3_path,
                "storage": "r2",
                "ticker": ticker
            }
        except Exception as e:
            print(f"R2 upload failed, falling back to local: {e}")

    # Fallback to local file
    try:
        os.makedirs("outputs", exist_ok=True)
        local_path = f"outputs/brief_{ticker}_{timestamp}.md"
        with open(local_path, "w") as f:
            f.write(content)
        return {
            "error": False,
            "file_path": local_path,
            "storage": "local",
            "ticker": ticker
        }
    except Exception as e:
        return {"error": True, "message": str(e)}