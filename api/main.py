"""
FastAPI REST API for Citation Intent Classification

This module provides a RESTful API endpoint for classifying citation intents.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
import os
import logging
from classifier import CitationIntentClassifier

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Citation Intent Classification API",
    description="Classify citation intents in scientific papers using LLMs",
    version="1.0.0"
)

# Global classifier instance
classifier: Optional[CitationIntentClassifier] = None


class CitationRequest(BaseModel):
    """Request model for citation classification."""
    text: str = Field(..., description="Full text containing the citation")
    cite_start: int = Field(..., ge=0, description="Start position of citation (0-indexed)")
    cite_end: int = Field(..., gt=0, description="End position of citation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "The apparent success of an approach based on a combination of large corpora and relatively simple heuristics is consistent with the conclusions reached in a number of earlier investigations (Banko and Brill, 2001; Lapata and Keller, 2004).",
                "cite_start": 178,
                "cite_end": 223
            }
        }


class CitationResponse(BaseModel):
    """Response model for citation classification."""
    citation_context: str = Field(..., description="Processed text with @@CITATION@@ tag")
    raw_prediction: str = Field(..., description="Raw model output")
    predicted_class: Optional[str] = Field(..., description="Cleaned class label")
    valid: bool = Field(..., description="Whether prediction is valid")
    model: str = Field(..., description="Model name used")
    dataset: str = Field(..., description="Dataset configuration")


class ConfigResponse(BaseModel):
    """Response model for configuration."""
    model: str
    dataset: str
    system_prompt_id: int
    query_template: str
    temperature: float
    class_labels: list


def ensure_classifier_initialized():
    """Ensure the classifier is initialized and ready."""
    global classifier
    if classifier is None:
        config_path = Path(__file__).parent / "config.json"
        classifier = CitationIntentClassifier(config_path)
        print(f"Initialized classifier with model: {classifier.model_name}")
        print(f"Connected to inference API: {classifier.config['inference_api']['base_url']}")


@app.on_event("startup")
async def startup_event():
    """Initialize classifier on startup."""
    print("Initializing Citation Intent Classification API...")
    try:
        ensure_classifier_initialized()
        print("API ready!")
    except Exception as e:
        print(f"Warning: Could not initialize classifier: {e}")
        print("Classifier will be initialized on first request")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Citation Intent Classification API",
        "version": "1.0.0",
        "endpoints": {
            "classify": "/classify",
            "config": "/config",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "citation-intent-classifier"
    }


@app.post("/classify", response_model=CitationResponse, tags=["Classification"])
async def classify_citation(request: CitationRequest):
    """
    Classify a citation's intent.
    
    - **text**: Full text with citation
    - **cite_start**: Start position of citation (0-indexed)
    - **cite_end**: End position of citation
    
    Returns the predicted citation intent class.
    """
    try:
        # Ensure classifier is ready
        ensure_classifier_initialized()
        
        # Validate cite positions
        if request.cite_start >= request.cite_end:
            raise HTTPException(
                status_code=400,
                detail="cite_start must be less than cite_end"
            )
        
        if request.cite_end > len(request.text):
            raise HTTPException(
                status_code=400,
                detail=f"cite_end ({request.cite_end}) exceeds text length ({len(request.text)})"
            )
        
        # Classify citation
        result = classifier.classify(
            text=request.text,
            cite_start=request.cite_start,
            cite_end=request.cite_end
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config", response_model=ConfigResponse, tags=["Configuration"])
async def get_config():
    """Get current API configuration."""
    try:
        ensure_classifier_initialized()
        return {
            "model": classifier.model_name,
            "dataset": classifier.config['dataset'],
            "system_prompt_id": classifier.config['system_prompt_id'],
            "query_template": classifier.config['query_template'],
            "temperature": classifier.config['temperature'],
            "class_labels": classifier.class_labels
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # Load configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    try:
        logger.info(f"Starting Citation Intent Classification API on {host}:{port}")
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            log_level=log_level,
            reload=False,
            access_log=True
        )
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        exit(1)
