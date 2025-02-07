from pathlib import Path
import base64
from typing import Dict, List
from ai_suite.extraction.invoice_model import InvoiceData
from ai_suite.llm_utils.llm_factory import LLMFactory
from ai_suite.ie.utils.json_utils import save_json

class InvoiceExtractor:
    def __init__(self):
        self.llm = LLMFactory("openai")
        
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def extract_invoice_data(self, image_path: str, model: str = "gpt-4o-mini", normalize: bool = True, save_output: bool = True) -> InvoiceData:
        """Extract structured data from invoice image using GPT-4 Vision."""
        # Encode image
        base64_image = self.encode_image(image_path)
        
        # Add normalization instruction if needed
        system_content = """You are an expert invoice data extraction assistant. 
        Extract the required information from the invoice image and format it according to the specified structure.
        Be precise and accurate with numbers and dates."""
        
        if normalize:
            system_content += """
            Please normalize the data as follows:
            - Dates should be in ISO format (YYYY-MM-DD)
            - Numbers should use period as decimal separator
            - Remove any currency symbols and use plain numbers
            - Standardize units and quantities
            """
        
        # Prepare messages for LLM with image
        messages = [
            {
                "role": "system",
                "content": system_content
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Please extract the following information from this invoice image:
                        - Client name and address
                        - Invoice date
                        - All items with their descriptions, quantities, prices per unit, and total amounts
                        - Total invoice value"""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        # Get structured data using LLM
        try:
            result = self.llm.create_completion(
                response_model=InvoiceData,
                messages=messages,
                model=model,
                temperature=0.0,
                max_tokens=1000
            )
            
            # Save the extracted data if requested
            if save_output:
                input_path = Path(image_path)
                output_path = input_path.parent.parent / "extracted" / f"{input_path.stem}.json"
                save_json(result.model_dump(), output_path)
                
            return result
        except Exception as e:
            raise Exception(f"Error extracting invoice data: {str(e)}")

def main():
    # Example usage
    extractor = InvoiceExtractor()
    
    # Process a single invoice
    #invoice_path = "ai_suite/extraction/data/invoice_hf/images/invoice_000.png"


    # process list of invoices
    invoice_paths = list(Path("ai_suite/extraction/data/invoice_hf/images").glob("*.png"))
    # get first 5 invoices
    invoice_paths = invoice_paths[1:5]
    for invoice_path in invoice_paths:
        try:
            invoice_data = extractor.extract_invoice_data(invoice_path)
            print(f"Extracted data: {invoice_data.model_dump_json(indent=2)}")
        except Exception as e:
            print(f"Error processing invoice: {str(e)}")

if __name__ == "__main__":
    main() 