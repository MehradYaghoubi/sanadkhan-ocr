import io
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from secrets import token_urlsafe

from fastapi.testclient import TestClient
from PIL import Image

from app.dependencies import get_extraction_service
from app.main import app


def test_extract_with_configured_vision_provider(monkeypatch):
    key = token_urlsafe(16)
    received = []

    class Provider(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            received.append((self.path, self.headers["Authorization"], payload["model"]))
            assert "data:image/jpeg;base64," in json.dumps(payload)
            result = {"doc_type": "national_card", "fields": {}, "raw_text": "Synthetic document"}
            body = json.dumps({"choices": [{"message": {"content": json.dumps(result)}}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    with ThreadingHTTPServer(("127.0.0.1", 0), Provider) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        monkeypatch.setenv("SANADKHAN_API_BASE", f"http://127.0.0.1:{server.server_port}/v1")
        monkeypatch.setenv("SANADKHAN_MODEL", "synthetic-vision")
        monkeypatch.setenv("SANADKHAN_API_KEY", key)
        get_extraction_service.cache_clear()
        try:
            with TestClient(app) as client:
                assert key not in client.get("/").text
                assert client.get("/api/document-types").status_code == 200
                image = io.BytesIO()
                Image.new("RGB", (200, 120), "white").save(image, "JPEG")
                result = client.post("/api/extract", files={"file": ("synthetic.jpg", image.getvalue(), "image/jpeg")}, data={"doc_type": "national_card"})
                assert result.status_code == 200, result.text
                assert result.json()["raw_text"] == "Synthetic document"
                assert key not in result.text
                assert received == [("/v1/chat/completions", f"Bearer {key}", "synthetic-vision")]
        finally:
            get_extraction_service.cache_clear()
            server.shutdown()
            thread.join()
