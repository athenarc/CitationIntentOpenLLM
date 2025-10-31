# Citation Intent Classification API

A lightweight FastAPI-based REST API for classifying citation intents using open-source LLMs through any OpenAI-compatible inference API.

## Overview

This API provides a simple interface to classify citation intents in scientific papers. It reuses the helper functions from the experimental pipeline but operates as a standalone service with a single configuration (no parameter looping).

**Infrastructure-agnostic design**: Works with any OpenAI-compatible inference service including:
- [Text Generation Inference (TGI)](https://github.com/huggingface/text-generation-inference)
- [vLLM](https://github.com/vllm-project/vllm)
- [LM Studio](https://lmstudio.ai/)
- [LocalAI](https://github.com/mudler/LocalAI)
- OpenAI API
- And more...

## Features

- **FastAPI-based REST API**: Modern, fast, and easy to use
- **Single prediction endpoint**: Classify individual citations on demand
- **Infrastructure-agnostic**: Works with TGI, vLLM, LM Studio, or any OpenAI-compatible API
- **Configurable models**: Use any LLM that supports chat completions
- **Dataset-specific prompts**: Support for SciCite and ACL-ARC datasets
- **Automatic label cleaning**: Handles various model output formats
- **Interactive documentation**: Auto-generated Swagger UI at `/docs`

## Setup

### Prerequisites

- Python 3.8+
- An inference server running an OpenAI-compatible API (TGI, vLLM, etc.)
- API access credentials (if required by your inference server)

### Installation

1. **Install Python dependencies:**

```bash
cd api
pip install -r requirements.txt
```

2. **Set up your inference server:**

Choose one of the following options:

**Option A: Text Generation Inference (TGI)**
```bash
# Using Docker
docker run -p 8080:80 -v $PWD/models:/data ghcr.io/huggingface/text-generation-inference:latest \
  --model-id Qwen/Qwen2.5-14B-Instruct
```

**Option B: vLLM**
```bash
# Using pip installation
vllm serve Qwen/Qwen2.5-14B-Instruct --port 8080
```

**Option C: LM Studio**
```bash
# Download model and start server
lms get lmstudio-community/Qwen2.5-14B-Instruct-GGUF/Qwen2.5-14B-Instruct-Q8_0.gguf
lms server start
```

3. **Configure the API:**

Edit `config.json` to point to your inference server:

```json
{
    "inference_api": {
        "base_url": "http://localhost:8080/v1",
        "api_key": "your-api-key-here",
        "model_name": "Qwen/Qwen2.5-14B-Instruct"
    },
    "dataset": "scicite",
    "system_prompt_id": 3,
    "prompting_method": "zero-shot",
    "examples_method": "1-inline",
    "examples_seed": 42,
    "query_template": "1-simple",
    "temperature": 0.0,
    "max_tokens": 15
}
```

**Configuration parameters:**

*Inference Settings:*
- `inference_api.base_url`: URL of your inference server's API endpoint (must be OpenAI-compatible)
- `inference_api.api_key`: API key if required (use empty string if not needed)
- `inference_api.model_name`: Model identifier to use for inference

*Task Configuration:*
- `dataset`: Either `"scicite"` or `"acl-arc"`
- `system_prompt_id`: System prompt variant (1, 2, or 3)

*Prompting Strategy:*
- `prompting_method`: `"zero-shot"` (0 examples), `"one-shot"` (1 example), `"few-shot"` (5 examples), or `"many-shot"` (10 examples)
- `examples_method`: `"1-inline"` (append to system prompt) or `"2-roles"` (user/assistant pairs). Only used if prompting_method is not zero-shot
- `examples_seed`: Random seed for example selection (default: 42)

*Output Format:*
- `query_template`: `"1-simple"` (direct class prediction) or `"2-qa-multiple-choice"` (letter-based QA)
- `temperature`: Sampling temperature (0.0 to 1.0)
- `max_tokens`: Maximum tokens in model response (default: 15)

## Usage

### Starting the API

**Method 1: Using Python directly**

```bash
cd api
python main.py
```

**Method 2: Using Uvicorn**

```bash
cd api
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`

### Interactive Documentation

Visit `http://localhost:8000/docs` for the auto-generated Swagger UI where you can:
- View all endpoints
- Test the API interactively
- See request/response schemas

### Making Requests

**Using curl:**

```bash
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d @example_input.json
```

Or inline:

```bash
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The apparent success of an approach based on a combination of large corpora and relatively simple heuristics is consistent with the conclusions reached in a number of earlier investigations (Banko and Brill, 2001; Lapata and Keller, 2004).",
    "cite_start": 178,
    "cite_end": 223
  }'
```

**Using Python requests:**

```python
import requests
import json

url = "http://localhost:8000/classify"

data = {
    "text": "The apparent success of an approach based on a combination of large corpora and relatively simple heuristics is consistent with the conclusions reached in a number of earlier investigations (Banko and Brill, 2001; Lapata and Keller, 2004).",
    "cite_start": 178,
    "cite_end": 223
}

response = requests.post(url, json=data)
result = response.json()

print(f"Predicted class: {result['predicted_class']}")
print(f"Citation context: {result['citation_context']}")
```

**Example response:**

```json
{
  "citation_context": "The apparent success of an approach based on a combination of large corpora and relatively simple heuristics is consistent with the conclusions reached in a number of earlier investigations @@CITATION@@.",
  "raw_prediction": "results comparison",
  "predicted_class": "results comparison",
  "valid": true,
  "model": "QWEN2.5_14B",
  "dataset": "scicite"
}
```

## API Endpoints

### `POST /classify`

Classify a citation's intent.

**Request Body:**
```json
{
  "text": "Full text containing citation",
  "cite_start": 100,
  "cite_end": 120
}
```

**Response:**
```json
{
  "citation_context": "Text with @@CITATION@@ tag",
  "raw_prediction": "Model output",
  "predicted_class": "Cleaned class label",
  "valid": true,
  "model": "Model name",
  "dataset": "Dataset type"
}
```

### `GET /config`

Get current API configuration.

**Response:**
```json
{
  "model": "QWEN2.5_14B",
  "dataset": "scicite",
  "system_prompt_id": 3,
  "query_template": "1-simple",
  "temperature": 0.0,
  "class_labels": ["background information", "method", "results comparison"]
}
```

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "citation-intent-classifier"
}
```

### `GET /`

Root endpoint with API information.

### `GET /docs`

Interactive Swagger UI documentation (auto-generated by FastAPI).

## Class Labels

### SciCite Dataset
- `background information`: Background context about a problem or concept
- `method`: Using a method, tool, or dataset
- `results comparison`: Comparing results with other work

### ACL-ARC Dataset
- `BACKGROUND`: Background information from cited paper
- `MOTIVATION`: Paper is motivated by cited work
- `USES`: Uses methodology or tools from cited paper
- `EXTENDS`: Extends methods/tools/data from cited paper
- `COMPARES_CONTRASTS`: Compares or contrasts with cited paper
- `FUTURE`: Cited paper is potential future work

## Architecture

```
api/
├── main.py                 # FastAPI application
├── classifier.py           # Core classification logic
├── config.json             # Configuration file
├── requirements.txt        # Python dependencies
├── example_input.json      # Example request
└── README.md              # This file
```

The API:
1. Loads configuration from `config.json`
2. Connects to LM Studio's OpenAI-compatible endpoint
3. Preprocesses citations by replacing spans with `@@CITATION@@`
4. Sends prompts to the model via the classifier
5. Cleans and validates predictions
6. Returns structured JSON responses

## System Prompts

Three prompt variants are available for each dataset (configured via `system_prompt_id`):

- **SP1**: Minimal instructions
- **SP2**: Structured with markdown headers
- **SP3**: Most explicit with exact output format (recommended)

System prompts are loaded from `../experimental-configs/system_prompts.json`.

## Query Templates

- **1-simple**: Direct class prediction (`"Text \nClass:"`)
- **2-qa-multiple-choice**: Multiple choice format with lettered options

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid parameters)
- `500`: Internal server error

The API returns `null` for `predicted_class` if:
- Model output doesn't match any class label
- Multiple class labels appear in output
- Output format is ambiguous

Check the `valid` field in responses to verify successful classification.

## Performance

Inference time depends on:
- Model size (larger models = slower but more accurate)
- Context length setting
- GPU availability
- Temperature (higher = more sampling overhead)

Typical inference time: 2-5 seconds per citation on GPU.

## Troubleshooting

**Model not loading:**
- Verify model path in `config.json`
- Check LM Studio server is running: `lms server status`
- Ensure sufficient GPU memory

**Port conflicts:**
- Change port in startup command: `uvicorn main:app --port 8001`
- Verify LM Studio is on port 1234 (or update `config.json`)

**Invalid predictions:**
- Try temperature=0.0 for more deterministic outputs
- Use system_prompt_id=3 (most explicit)
- Check if citation positions are correct
- Verify text encoding (should be UTF-8)

**Dependencies not found:**
- Make sure you're in the `api` directory
- Run `pip install -r requirements.txt`
- Use a virtual environment to avoid conflicts

## Development

**Enable auto-reload during development:**

```bash
uvicorn main:app --reload
```

**Run with custom host/port:**

```bash
uvicorn main:app --host 127.0.0.1 --port 8080
```

**View logs:**

The API logs startup information and warnings to stdout.

## Differences from Experimental Pipeline

| Feature | Experimental Pipeline | API |
|---------|----------------------|-----|
| Purpose | Batch evaluation | Single predictions |
| Configuration | Multiple parameter combinations | Single configuration |
| Output | CSV files with metrics | JSON responses |
| Model loading | Per experiment | On startup |
| Interface | Command-line script | REST API |
| Use case | Research & benchmarking | Production inference |

## Testing

Test the API with the example input:

```bash
cd api
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d @example_input.json
```

Expected output should show:
- `citation_context` with `@@CITATION@@` tag
- `predicted_class` as one of the valid labels
- `valid` as `true`

## License

Same license as the main CitationIntentOpenLLM project.
