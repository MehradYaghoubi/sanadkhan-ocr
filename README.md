# Sanadkhan | Persian Document OCR

Sanadkhan extracts structured fields from Persian document images using a configurable vision model. It offers a right-to-left browser interface, document cropping and field selection, and a FastAPI endpoint for JSON results.

## Run locally

Install Python 3.11 or newer. Then install the requirements and set the server environment in PowerShell 7.

```powershell
python -m pip install -r requirements.txt
$env:SANADKHAN_API_BASE = 'https://your-provider.example/v1'
$env:SANADKHAN_MODEL = 'your-vision-model'
$env:SANADKHAN_API_KEY = Read-Host 'Vision API key' -MaskInput
python run.py
```

Open http://127.0.0.1:8035. API docs are available at /docs. The provider must implement OpenAI-compatible chat completions with image input. The key stays on the server. Use synthetic or authorized images because extraction sends image data to the configured provider. The local server binds to loopback by default.

## Main endpoints

- GET /api/document-types lists supported schemas.
- POST /api/extract accepts a multipart image and returns structured results.
- POST /api/compose generates a preview from selected image regions.

## Check the integration locally

Run `python -m pip install pytest httpx` and `python -m pytest -q`. The test uses a synthetic image and a loopback vision provider.
