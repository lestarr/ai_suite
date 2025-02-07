from datasets import load_dataset
import pandas as pd
import os
import json
from PIL import Image
import io
import requests
import ast

# Create directories if they don't exist
base_dir = "data/invoice_hf"
image_dir = os.path.join(base_dir, "images")
json_dir = os.path.join(base_dir, "reference_jsons")

os.makedirs(image_dir, exist_ok=True)
os.makedirs(json_dir, exist_ok=True)

# Load dataset
dataset = load_dataset("mychen76/invoices-and-receipts_ocr_v1")
train_dataset = dataset['train']

# Get first 100 samples
for i, sample in enumerate(train_dataset.select(range(100))):
    # Save image
    image = sample['image']
    image_path = os.path.join(image_dir, f"invoice_{i:03d}.png")
    image.save(image_path)
    
    # Save JSON
    parsed_data = sample['parsed_data']
    try:
        # The parsed_data contains a dictionary with 'xml', 'json', and 'kie' keys
        # First, safely evaluate the string to a dictionary
        parsed_dict = ast.literal_eval(parsed_data)
        
        # The 'json' key contains another string that needs to be parsed
        json_str = parsed_dict['json']
        json_data = ast.literal_eval(json_str)
        
        json_path = os.path.join(json_dir, f"invoice_{i:03d}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"Error processing JSON for sample {i}: {e}")
        continue
    
    if (i + 1) % 10 == 0:
        print(f"Processed {i + 1} samples")

print("Download completed!")
