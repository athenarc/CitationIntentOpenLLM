"""
Citation Intent Classification API

This module provides a lightweight API for classifying citation intents using LLMs.
It reuses helper functions from the experimental pipeline but operates as a standalone service.
"""

import sys
import os
import json
from pathlib import Path
from openai import OpenAI
import string

# Add parent directory to path to import from experimental code
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_config(config_path="config.json"):
    """Load API configuration from JSON file."""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    return json.loads(config_file.read_text())


def load_system_prompts(dataset):
    """Load system prompts from experimental configs."""
    system_prompts_path = Path(__file__).parent.parent / 'experimental-configs' / 'system_prompts.json'
    system_prompts = json.loads(system_prompts_path.read_text())
    return system_prompts


def get_class_labels(dataset):
    """Get class labels for the specified dataset."""
    class_labels = {
        "scicite": ["background information", "method", "results comparison"],
        "acl-arc": ["BACKGROUND", "MOTIVATION", "USES", "EXTENDS", "COMPARES_CONTRASTS", "FUTURE"]
    }
    return class_labels.get(dataset, [])


def form_multiple_choice_prompt(class_labels):
    """Generate multiple choice options from class labels."""
    return '\n'.join([f"{letter}) {label}" for letter, label in zip(string.ascii_lowercase, class_labels)])


def preprocess_citation(text, cite_start, cite_end):
    """
    Replace citation span with @@CITATION@@ tag.
    
    Args:
        text: Full text containing the citation
        cite_start: Start position of citation
        cite_end: End position of citation
    
    Returns:
        Processed text with @@CITATION@@ tag
    """
    cite_tag = "@@CITATION@@"
    # Remove newlines and replace citation span with tag
    text = text.replace('\n', ' ')
    processed_text = f"{text[:cite_start]}{cite_tag}{text[cite_end:]}"
    return processed_text


def get_prediction(client, system_prompt, model_path, sentence, query_template, temperature, max_tokens, multiple_choice=None):
    """
    Get citation intent prediction from the model.
    
    Args:
        client: OpenAI client instance
        system_prompt: System prompt configuration
        model_path: Path to the model
        sentence: Citation context to classify
        query_template: Query template type ('1-simple' or '2-qa-multiple-choice')
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        multiple_choice: Multiple choice options (for QA template)
    
    Returns:
        Predicted class label
    """
    template_qa = "{sentence}\n### Question: Which is the most likely intent for this citation? \n{options}\n### Answer:"
    template_simple = "{sentence} \nClass:"
    
    prompt = template_qa if query_template[0] == '2' else template_simple
    
    message = system_prompt + [{
        "role": "user", 
        "content": prompt.format(sentence=sentence, options=multiple_choice if multiple_choice else "")
    }]
    
    completion = client.chat.completions.create(
        model=model_path,
        messages=message,
        max_tokens=max_tokens,
        temperature=temperature
    )
    
    predicted_class = completion.choices[0].message.content.strip()
    return predicted_class


def clean_prediction(prediction, class_labels):
    """
    Clean model output to extract the predicted class.
    
    Args:
        prediction: Raw model output
        class_labels: List of valid class labels
    
    Returns:
        Cleaned class label or None if invalid
    """
    # Map letters to labels for multiple choice responses
    letter_to_label = {letter: label for letter, label in zip(string.ascii_lowercase, class_labels)}
    
    stripped_text = prediction.lower().strip().rstrip(')')
    
    # Check if response is a single letter
    if stripped_text in letter_to_label:
        return letter_to_label[stripped_text]
    
    # Count occurrences of each label in the response
    count_labels = {label: prediction.lower().count(label.lower()) for label in class_labels}
    if sum(count_labels.values()) == 1:
        return next(label for label, count in count_labels.items() if count == 1)
    
    # If exact match found (case insensitive)
    for label in class_labels:
        if label.lower() == stripped_text:
            return label
    
    return None


class CitationIntentClassifier:
    """Main classifier class for citation intent classification."""
    
    def __init__(self, config_path="config.json"):
        """Initialize the classifier with configuration."""
        self.config = load_config(config_path)
        
        # Initialize OpenAI client for any OpenAI-compatible API (TGI, vLLM, etc.)
        inference_config = self.config['inference_api']
        self.client = OpenAI(
            base_url=inference_config['base_url'], 
            api_key=inference_config['api_key']
        )
        self.model_name = inference_config['model_name']
        
        # Load prompts and labels
        dataset = self.config['dataset']
        system_prompts = load_system_prompts(dataset)
        prompt_id = f"{dataset}{self.config['system_prompt_id']}"
        
        self.system_prompt = [{
            "role": "system",
            "content": system_prompts[prompt_id]
        }]
        
        self.class_labels = get_class_labels(dataset)
        self.multiple_choice = None
        
        if self.config['query_template'][0] == '2':
            self.multiple_choice = form_multiple_choice_prompt(self.class_labels)
    
    def classify(self, text, cite_start, cite_end):
        """
        Classify a citation's intent.
        
        Args:
            text: Full text containing the citation
            cite_start: Start position of citation
            cite_end: End position of citation
        
        Returns:
            Dictionary with prediction results
        """
        # Preprocess citation
        citation_context = preprocess_citation(text, cite_start, cite_end)
        
        # Get raw prediction
        raw_prediction = get_prediction(
            client=self.client,
            system_prompt=self.system_prompt,
            model_path=self.model_name,
            sentence=citation_context,
            query_template=self.config['query_template'],
            temperature=self.config['temperature'],
            max_tokens=self.config['max_tokens'],
            multiple_choice=self.multiple_choice
        )
        
        # Clean prediction
        cleaned_prediction = clean_prediction(raw_prediction, self.class_labels)
        
        return {
            "citation_context": citation_context,
            "raw_prediction": raw_prediction,
            "predicted_class": cleaned_prediction,
            "valid": cleaned_prediction is not None,
            "model": self.model_name,
            "dataset": self.config['dataset']
        }
