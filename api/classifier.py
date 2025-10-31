"""
Citation Intent Classification API

This module provides a lightweight API for classifying citation intents using LLMs.
It reuses helper functions from the experimental pipeline but operates as a standalone service.
"""

import sys
import os
import json
import random
import string
from pathlib import Path
from openai import OpenAI
import pandas as pd

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


def get_num_examples(prompting_method):
    """Get number of examples based on prompting method."""
    examples_map = {
        "zero-shot": 0,
        "one-shot": 1,
        "few-shot": 5,
        "many-shot": 10
    }
    return examples_map.get(prompting_method, 0)


def load_training_data(dataset):
    """Load training data for examples."""
    train_path = Path(__file__).parent.parent / 'datasets' / 'formatted' / dataset / 'train.csv'
    if not train_path.exists():
        raise FileNotFoundError(f"Training data not found: {train_path}")
    return pd.read_csv(train_path)


def add_examples(num_examples, query_template, examples_method, examples_seed, df_train, system_prompt, class_labels):
    """
    Add few-shot examples to the system prompt.
    
    Args:
        num_examples: Number of examples per class
        query_template: Query template type
        examples_method: How to inject examples ('1-inline' or '2-roles')
        examples_seed: Random seed for example selection
        df_train: Training dataframe
        system_prompt: System prompt messages
        class_labels: List of class labels
    
    Returns:
        Updated system prompt with examples
    """
    if num_examples == 0:
        return system_prompt
    
    all_example_pairs = []
    random.seed(examples_seed)
    
    template_qa = "{sentence}\n### Question: Which is the most likely intent for this citation?\n{options}\n### Answer: "
    template_simple = "{sentence} \nClass: "
    multiple_choice = form_multiple_choice_prompt(class_labels) if query_template[0] == '2' else None
    prompt = template_qa if query_template[0] == '2' else template_simple

    if examples_method[0] == '1':  # Inline method
        all_example_pairs = [
            f"\n{prompt.format(sentence=ex, options=multiple_choice if multiple_choice else '')} {label}\n" 
            for label in class_labels
            for ex in df_train[df_train['citation_class_label'] == label].sample(num_examples, random_state=examples_seed)['citation_context']
        ]
        random.shuffle(all_example_pairs)
        all_example_pairs = ''.join(all_example_pairs)
        system_prompt[0]['content'] += "\n\n########\n\n# EXAMPLES #\n" + all_example_pairs

    elif examples_method[0] == '2':  # Roles method (alternating user/assistant)
        all_example_pairs = [
            [
                {"role": "user", "content": f"{prompt.format(sentence=ex, options=multiple_choice if multiple_choice else '')}"},
                {"role": "assistant", "content": label}
            ]
            for label in class_labels
            for ex in df_train[df_train['citation_class_label'] == label].sample(num_examples, random_state=examples_seed)['citation_context']
        ]
        random.shuffle(all_example_pairs)
        system_prompt.extend([pair for sublist in all_example_pairs for pair in sublist])

    return system_prompt


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
        
        # Add few-shot examples if prompting method requires it
        prompting_method = self.config.get('prompting_method', 'zero-shot')
        num_examples = get_num_examples(prompting_method)
        
        if num_examples > 0:
            examples_method = self.config.get('examples_method', '1-inline')
            examples_seed = self.config.get('examples_seed', 42)
            df_train = load_training_data(dataset)
            
            self.system_prompt = add_examples(
                num_examples=num_examples,
                query_template=self.config['query_template'],
                examples_method=examples_method,
                examples_seed=examples_seed,
                df_train=df_train,
                system_prompt=self.system_prompt.copy(),  # Copy to avoid modifying original
                class_labels=self.class_labels
            )
    
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
        
        # Gather prompt info for verification from config
        prompting_method = self.config['prompting_method']
        examples_method = self.config['examples_method']
        num_examples = get_num_examples(prompting_method)
        
        return {
            "citation_context": citation_context,
            "raw_prediction": raw_prediction,
            "predicted_class": cleaned_prediction,
            "valid": cleaned_prediction is not None,
            "model": self.model_name,
            "dataset": self.config['dataset'],
            "prompt_info": {
                "prompting_method": prompting_method,
                "examples_method": examples_method,
                "num_messages_in_prompt": len(self.system_prompt),
                "examples_per_class": num_examples,
                "total_expected_examples": num_examples * len(self.class_labels)
            }
        }
