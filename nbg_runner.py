import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Render가 제공하는 PORT 사용
    uvicorn.run("nbg_server:app_mount", host="0.0.0.0", port=port)
