# utils/excel_reader.py
import pandas as pd
from io import BytesIO
import streamlit as st

def extract_excel_text(file):
    """
    Extract text from Excel files (.xlsx, .xls)
    
    Args:
        file: Uploaded Excel file
        
    Returns:
        Extracted text as string or None if error
    """
    try:
        # Read all sheets
        excel_file = pd.ExcelFile(file)
        all_text = []
        
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file, sheet_name=sheet_name)
            
            # Add sheet name as header
            all_text.append(f"\n--- Sheet: {sheet_name} ---\n")
            
            # Convert dataframe to text representation
            # Get column headers
            headers = df.columns.tolist()
            all_text.append(" | ".join([str(h) for h in headers]))
            
            # Get row data
            for _, row in df.iterrows():
                row_text = " | ".join([str(val) for val in row.values])
                all_text.append(row_text)
        
        return "\n".join(all_text)
        
    except Exception as e:
        st.error(f"Error reading Excel file: {str(e)}")
        return None

def create_translated_excel(translated_text, original_filename):
    """
    Create a new Excel file with translated content
    
    Args:
        translated_text: Translated text content
        original_filename: Original filename for reference
        
    Returns:
        BytesIO buffer containing Excel file
    """
    buffer = BytesIO()
    
    try:
        # Parse the translated text back into a structured format
        lines = translated_text.split('\n')
        current_sheet = None
        sheet_data = []
        headers = None
        
        # Create a dictionary to store sheet data
        sheets_dict = {}
        
        for line in lines:
            if line.startswith('--- Sheet:') and line.endswith('---'):
                # Save previous sheet if exists
                if current_sheet and sheet_data:
                    df = pd.DataFrame(sheet_data, columns=headers) if headers else pd.DataFrame(sheet_data)
                    sheets_dict[current_sheet] = df
                
                # Start new sheet
                current_sheet = line.replace('--- Sheet:', '').replace('---', '').strip()
                sheet_data = []
                headers = None
                
            elif ' | ' in line and current_sheet:
                parts = line.split(' | ')
                
                # If headers not set and this looks like headers (all strings, no numbers)
                if headers is None and all(not p.replace('.', '').replace('-', '').isdigit() for p in parts):
                    headers = parts
                else:
                    # Convert numeric strings back to appropriate types
                    row = []
                    for p in parts:
                        try:
                            # Try to convert to float if possible
                            if p.replace('.', '').replace('-', '').isdigit():
                                if '.' in p:
                                    row.append(float(p))
                                else:
                                    row.append(int(p))
                            else:
                                row.append(p)
                        except:
                            row.append(p)
                    sheet_data.append(row)
        
        # Save the last sheet
        if current_sheet and sheet_data:
            df = pd.DataFrame(sheet_data, columns=headers) if headers else pd.DataFrame(sheet_data)
            sheets_dict[current_sheet] = df
        
        # Create Excel file with multiple sheets
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            for sheet_name, df in sheets_dict.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Add metadata sheet
            metadata = pd.DataFrame({
                'Info': ['Original File', 'Translation Date', 'Note'],
                'Value': [original_filename, 
                         pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                         'Translated by Sabio Translate']
            })
            metadata.to_excel(writer, sheet_name='Translation Info', index=False)
        
    except Exception as e:
        # If parsing fails, create a simple CSV-like structure
        df = pd.DataFrame([line.split('\n') for line in translated_text.split('\n')])
        df.to_excel(buffer, index=False, header=False)
    
    buffer.seek(0)
    return buffer

def is_excel_file(filename):
    """Check if file is an Excel file"""
    return filename.endswith(('.xlsx', '.xls', '.xlsm'))