import streamlit as st
import pandas as pd
from pathlib import Path
import json
from ai_suite.extraction.invoice_extraction import InvoiceExtractor
import matplotlib.pyplot as plt

st.title("Invoice Data Extraction")

# Initialize paths
base_dir = Path("ai_suite/extraction/data/invoice_hf")
images_dir = base_dir / "images"
extracted_dir = base_dir / "extracted"

# AI Client Selection and Settings
st.header("1. Settings")
col_client, col_norm = st.columns(2)

with col_client:
    ai_client = st.selectbox(
        "Select AI Client:",
        options=["gpt-4o", "gpt-4o-mini", "claude-3", "llama"],
        help="Choose the AI model for invoice processing"
    )

with col_norm:
    normalize_data = st.checkbox(
        "Normalize Data",
        value=True,
        help="Standardize formats for dates, numbers, and currencies"
    )

# Data Loading Section
st.header("2. Invoice Processing")

# Create two columns for different processing options
col1, col2 = st.columns(2)

with col1:
    st.subheader("Process Selected")
    # List available invoice images
    invoice_files = list(images_dir.glob("*.png"))
    selected_invoices = st.multiselect(
        "Select invoices to process:",
        options=[f.name for f in invoice_files],
        default=[invoice_files[0].name if invoice_files else None]
    )
    
    # Process Selected Button
    if st.button("Process Selected"):
        extractor = InvoiceExtractor()
        
        progress_bar = st.progress(0)
        for idx, invoice_name in enumerate(selected_invoices):
            try:
                image_path = images_dir / invoice_name
                invoice_data = extractor.extract_invoice_data(
                    str(image_path),
                    model=ai_client,
                    normalize=normalize_data
                )
                st.success(f"Processed {invoice_name}")
            except Exception as e:
                st.error(f"Error processing {invoice_name}: {str(e)}")
            
            # Update progress bar
            progress_bar.progress((idx + 1) / len(selected_invoices))
        
        st.success("Processing complete!")

with col2:
    st.subheader("Process All")
    total_invoices = len(invoice_files)
    st.write(f"Total invoices available: {total_invoices}")
    
    # Process All Button
    if st.button("Process All Invoices"):
        extractor = InvoiceExtractor()
        
        progress_bar = st.progress(0)
        for idx, invoice_path in enumerate(invoice_files):
            try:
                invoice_data = extractor.extract_invoice_data(
                    str(invoice_path),
                    model=ai_client,
                    normalize=normalize_data
                )
                st.success(f"Processed {invoice_path.name}")
            except Exception as e:
                st.error(f"Error processing {invoice_path.name}: {str(e)}")
            
            # Update progress bar
            progress_bar.progress((idx + 1) / total_invoices)
        
        st.success(f"Completed processing all {total_invoices} invoices!")

# Display Results
st.header("2. Extracted Data")

# Load and display extracted JSONs
if extracted_dir.exists():
    json_files = list(extracted_dir.glob("*.json"))
    if json_files:
        # Create a list to store all invoice data
        all_invoice_data = []
        
        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Add filename to the data
                data['filename'] = json_file.name
                all_invoice_data.append(data)
        
        # Convert to DataFrame
        df = pd.json_normalize(all_invoice_data)
        
        # Convert total_value to numeric
        df['total_value'] = pd.to_numeric(df['total_value'], errors='coerce')
        
        # Rename columns for better display
        column_mapping = {
            'filename': 'Invoice File',
            'client_name': 'Client Name',
            'client_address': 'Client Address',
            'invoice_date': 'Invoice Date',
            'total_value': 'Total Value'
        }
        df = df.rename(columns=column_mapping)
        
        # Display main invoice information
        st.subheader("Invoice Summary")
        st.dataframe(df[column_mapping.values()])
        
        # Display items for selected invoice
        st.subheader("Invoice Items")
        
        # Add tabs for individual/all items view
        tab1, tab2 = st.tabs(["Single Invoice Items", "All Items"])
        
        with tab1:
            selected_invoice = st.selectbox(
                "Select invoice to view items:",
                options=df['Invoice File'].tolist()
            )
            
            if selected_invoice:
                selected_data = next(d for d in all_invoice_data if d['filename'] == selected_invoice)
                items_df = pd.DataFrame(selected_data['items'])
                
                # Rename columns first
                items_column_mapping = {
                    'description': 'Description',
                    'quantity': 'Quantity',
                    'price_per_unit': 'Price per Unit',
                    'total_amount': 'Total Amount'
                }
                items_df = items_df.rename(columns=items_column_mapping)
                
                # Then convert numeric columns using the new column names
                numeric_columns = ['Quantity', 'Price per Unit', 'Total Amount']
                for col in numeric_columns:
                    items_df[col] = pd.to_numeric(items_df[col], errors='coerce')
                
                # Apply styling to center-align all cells
                styled_df = items_df.style.set_properties(**{
                    'text-align': 'center'
                }).format({
                    'Quantity': '{:.2f}',
                    'Price per Unit': '${:.2f}',
                    'Total Amount': '${:.2f}'
                })
                
                st.dataframe(styled_df, use_container_width=True)
                
                # Display visualizations only if we have numeric data
                if not items_df.empty and items_df['Price per Unit'].notna().any():
                    st.subheader("Visualizations")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Bar chart of item prices
                        fig1, ax1 = plt.subplots()
                        items_df.plot(kind='bar', x='Description', y='Price per Unit', ax=ax1)
                        plt.xticks(rotation=45)
                        plt.title('Price per Unit by Item')
                        st.pyplot(fig1)
                    
                    with col2:
                        # Pie chart of total amounts
                        fig2, ax2 = plt.subplots()
                        plt.pie(items_df['Total Amount'], labels=items_df['Description'], autopct='%1.1f%%')
                        plt.title('Distribution of Total Amounts')
                        st.pyplot(fig2)
                else:
                    st.warning("No numeric data available for visualization")
        
        with tab2:
            # Combine all items from all invoices
            all_items = []
            for invoice_data in all_invoice_data:
                items = pd.DataFrame(invoice_data['items'])
                items['Invoice'] = invoice_data['filename']  # Add invoice reference
                all_items.append(items)
            
            if all_items:
                # Combine all items into one DataFrame
                combined_items_df = pd.concat(all_items, ignore_index=True)
                
                # Rename columns
                items_column_mapping = {
                    'description': 'Description',
                    'quantity': 'Quantity',
                    'price_per_unit': 'Price per Unit',
                    'total_amount': 'Total Amount',
                    'Invoice': 'Invoice'
                }
                combined_items_df = combined_items_df.rename(columns=items_column_mapping)
                
                # Convert numeric columns
                numeric_columns = ['Quantity', 'Price per Unit', 'Total Amount']
                for col in numeric_columns:
                    combined_items_df[col] = pd.to_numeric(combined_items_df[col], errors='coerce')
                
                # Reorder columns to show Invoice first
                combined_items_df = combined_items_df[['Invoice', 'Description', 'Quantity', 'Price per Unit', 'Total Amount']]
                
                # Apply styling
                styled_combined_df = combined_items_df.style.set_properties(**{
                    'text-align': 'center'
                }).format({
                    'Quantity': '{:.2f}',
                    'Price per Unit': '${:.2f}',
                    'Total Amount': '${:.2f}'
                })
                
                st.dataframe(styled_combined_df, use_container_width=True)
                
                # Add summary statistics for all items
                st.subheader("All Items Summary")
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Items", len(combined_items_df))
                col2.metric("Total Value", f"${combined_items_df['Total Amount'].sum():,.2f}")
                col3.metric("Average Item Value", f"${combined_items_df['Total Amount'].mean():,.2f}")
            else:
                st.warning("No items data available")

        # Statistics
        st.subheader("Statistics")
        total_invoices = len(df)
        total_value = df['Total Value'].sum()
        avg_value = df['Total Value'].mean()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Invoices", total_invoices)
        col2.metric("Total Value", f"${total_value:,.2f}")
        col3.metric("Average Value", f"${avg_value:,.2f}")
        
    else:
        st.warning("No extracted data found. Please process some invoices first.")
else:
    st.warning("No extracted data directory found. Please process some invoices first.")

# Run the app
# if __name__ == "__main__":
#     st.run()

# streamlit run .\ai_suite\extraction\demo_app.py