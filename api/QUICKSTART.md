# Quick Start Guide - Citation Intent Classification API

## 5-Minute Setup

### 1. Install Dependencies

```bash
cd api
pip install -r requirements.txt
```

### 2. Start an Inference Server

Choose one of the following options:

**Option A: Using vLLM (Recommended for speed)**

```bash
# Install vLLM
pip install vllm

# Start server with a model
vllm serve Qwen/Qwen2.5-14B-Instruct --port 8080
```

**Option B: Using Text Generation Inference (TGI)**

```bash
# Using Docker
docker run -p 8080:80 -v $PWD/models:/data \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id Qwen/Qwen2.5-14B-Instruct
```

**Option C: Using LM Studio**

```bash
# Download model and start server
lms get lmstudio-community/Qwen2.5-14B-Instruct-GGUF/Qwen2.5-14B-Instruct-Q8_0.gguf
lms server start
```

### 3. Configure the API

Edit `config.json` to point to your inference server:

```json
{
    "inference_api": {
        "base_url": "http://localhost:8080/v1",
        "api_key": "",
        "model_name": "Qwen/Qwen2.5-14B-Instruct"
    },
    "dataset": "scicite",
    "system_prompt_id": 3,
    "query_template": "1-simple",
    "temperature": 0.0
}
```

### 4. Start the API

```bash
python main.py
```

The API will start on `http://localhost:8000`

### 5. Test the API

**Option A: Using the browser**

Visit `http://localhost:8000/docs` for interactive documentation

**Option B: Using curl**

```bash
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d @example_input.json
```

**Option C: Using the test script**

```bash
# Install requests if needed
pip install requests

# Run test suite
python test_api.py
```

**Option D: Using Python**

```python
import requests

url = "http://localhost:8000/classify"
data = {
    "text": "Recent work has shown that neural networks can learn to classify images (Smith et al., 2020).",
    "cite_start": 71,
    "cite_end": 88
}

response = requests.post(url, json=data)
print(response.json()['predicted_class'])
```

## Expected Output

```json
{
  "citation_context": "Text with @@CITATION@@ replacing the citation span",
  "raw_prediction": "Model's raw output",
  "predicted_class": "background information",
  "valid": true,
  "model": "QWEN2.5_14B",
  "dataset": "scicite"
}
```

## Common Issues

### Port Already in Use

```bash
# Use a different port
uvicorn main:app --port 8001
```

### Model Not Loading

1. Check model path in `config.json`
2. Verify model exists: `lms ls`
3. Check LM Studio server: `lms server status`

### LM Studio Not Found

```bash
# Install LM Studio CLI
# Visit: https://github.com/lmstudio-ai/lms
```

## Configuration Options

Edit `config.json` to customize:

- **Model**: Change `model.path` to use different models
- **Dataset**: Switch between `"scicite"` or `"acl-arc"`
- **Prompt**: Use `system_prompt_id` 1, 2, or 3 (3 is most explicit)
- **Temperature**: 0.0 for deterministic, higher for variety

## Next Steps

- View all endpoints: `http://localhost:8000/docs`
- Check configuration: `http://localhost:8000/config`
- Test with your own citations
- Integrate into your application

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/config` | GET | View configuration |
| `/classify` | POST | Classify citation |
| `/docs` | GET | Interactive documentation |

## Need Help?

- Check the full [README.md](README.md) for detailed documentation
- View interactive API docs at `/docs`
- Review example requests in `example_input.json`
- Run test suite with `python test_api.py`
