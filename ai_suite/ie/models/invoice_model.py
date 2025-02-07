from typing import List
from pydantic import BaseModel, Field
from datetime import date
from decimal import Decimal

class InvoiceItem(BaseModel):
    description: str = Field(description="Description of the product or service")
    quantity: Decimal = Field(description="Quantity of items")
    price_per_unit: Decimal = Field(description="Price per unit")
    total_amount: Decimal = Field(description="Total amount for this item")

class InvoiceData(BaseModel):
    client_name: str = Field(description="Name of the client/company being billed")
    client_address: str = Field(description="Complete address of the client")
    invoice_date: date = Field(description="Date of the invoice")
    items: List[InvoiceItem] = Field(description="List of products or services in the invoice")
    total_value: Decimal = Field(description="Total value of the invoice")
    
    class Config:
        json_schema_extra = {
            "example": {
                "client_name": "Acme Corp",
                "client_address": "123 Business St, Suite 100, City, State 12345",
                "invoice_date": "2024-03-20",
                "items": [
                    {
                        "description": "Web Development Services",
                        "quantity": 1,
                        "price_per_unit": 1000.00,
                        "total_amount": 1000.00
                    }
                ],
                "total_value": 1000.00
            }
        }
