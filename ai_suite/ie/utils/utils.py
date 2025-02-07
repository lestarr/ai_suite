import json
import re
from enum import Enum
from pydantic import BaseModel
import logging
import os
from datetime import datetime



def output(text, filename):
    """Write text to file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(str(text) + "\n")

def normalize_text(text):
    """
    Normalize the text by:
    - Removing leading/trailing whitespace
    - Converting to lowercase
    - Replacing newlines and multiple spaces with a single space
    """
    text = clean_markdown(text)
    
    # Convert to lowercase
    text = text.lower()

    # Replace newlines and multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)

    # replace "-" with " "
    text = re.sub(r'-', ' ', text)
    
    # remove punctuation 
    text = re.sub(r'[^\w\s]', '', text)
    
    return text.strip()

def clean_markdown(text):
    """
    Clean the input Markdown text by removing Markdown syntax.
    """
    # Remove Markdown links
    #text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # Remove Markdown headers
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    
    # Remove Markdown bold and italic
    text = re.sub(r'\*\*|__', '', text)
    text = re.sub(r'\*|_', '', text)
    
    # Remove Markdown code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # Remove Markdown inline code
    text = re.sub(r'`[^`\n]+`', '', text)
    
    # Remove Markdown lists
    text = re.sub(r'^\s*[-*+]\s', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s', '', text, flags=re.MULTILINE)
    
    # Remove extra whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = text.strip()
    
    return text

class TokenUsageTracker:
    def __init__(self, model_name: str):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.model_name = model_name
        
    def add_usage(self, usage):
        """Add token usage from an API call"""
        # Handle OpenAI usage format
        if hasattr(usage, 'usage'):
            usage = usage.usage
            
        # Handle different attribute names
        if hasattr(usage, 'prompt_tokens'):
            self.prompt_tokens += usage.prompt_tokens
        elif hasattr(usage, 'input_tokens'):
            self.prompt_tokens += usage.input_tokens
            
        if hasattr(usage, 'completion_tokens'):
            self.completion_tokens += usage.completion_tokens
        elif hasattr(usage, 'output_tokens'):
            self.completion_tokens += usage.output_tokens
        #logging.info(f"Added usage for {self.model_name}: {usage}")
    
    def get_total_tokens(self):
        """Get total tokens used"""
        return self.prompt_tokens + self.completion_tokens
    
    def get_cost(self):
        """Calculate total cost based on model and token usage"""
        if self.model_name == "gpt-4o":
            return self.prompt_tokens * 2.5/1000000 + self.completion_tokens * 10/1000000
        elif self.model_name == "gpt-4o-mini":
            return self.prompt_tokens * 0.15/1000000 + self.completion_tokens * 0.6/1000000
        elif self.model_name == "claude-3-5-sonnet-20240620":
            return self.prompt_tokens * 3/1000000 + self.completion_tokens * 15/1000000
        else:
            return 0
            #raise ValueError(f"Unsupported model: {self.model_name}")
    
    def get_summary(self):
        """Get usage summary"""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.get_total_tokens(),
            "cost_usd": round(self.get_cost(), 4)
        }

