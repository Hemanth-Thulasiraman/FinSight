import os
from datetime import datetime
def save_brief(ticker: str, content: str) -> dict:
    try:
        os.makedirs("outputs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"outputs/brief_{ticker}_{timestamp}.md"
        with open(file_path, "w") as f:
            f.write(content)
        return {"error": False, "file_path": file_path, "ticker": ticker}
    except Exception as e:
        return {"error": True, "message": str(e)}