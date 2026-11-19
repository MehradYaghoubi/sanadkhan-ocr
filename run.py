"""اجرای سرویس: python run.py"""

import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.getenv("SANADKHAN_HOST", "127.0.0.1"),
        port=int(os.getenv("SANADKHAN_PORT", "8035")),
    )
