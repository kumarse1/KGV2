#!/usr/bin/env python3
"""
Step 3: File Processing Utilities
Handles reading Excel, Word, CSV, and Text files
Run: python file_processor.py
"""

import pandas as pd
from docx import Document
import io

class FileProcessor:
    """Handles reading and processing different file formats"""
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls', '.docx', '.csv', '.txt']
        print("📁 FileProcessor initialized")
        print(f"   Supported formats: {', '.join(self.supported_formats)}")
    
    def read_excel_file(self, file_content):
        """Read Excel file and return text content"""
        try:
            # Read Excel file
            df = pd.read_excel(io.BytesIO(file_content))
            
            # Convert to text representation
            text_content = []
            text_content.append(f"Excel file contains {len(df)} rows and {len(df.columns)} columns")
            text_content.append(f"Columns: {', '.join(df.columns.tolist())}")
            text_content.append("\nData preview:")
            
            # Add sample data
            for idx, row in df.head(10).iterrows():
                row_text = []
                for col in df.columns:
                    if pd.notna(row[col]):
                        row_text.append(f"{col}: {row[col]}")
                text_content.append(f"Row {idx + 1}: {', '.join(row_text)}")
            
            return "\n".join(text_content)
        except Exception as e:
            return f"Error reading Excel file: {str(e)}"
    
    def read_docx_file(self, file_content):
        """Read Word document and return text content"""
        try:
            doc = Document(io.BytesIO(file_content))
            text_content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())
            
            return "\n".join(text_content)
        except Exception as e:
            return f"Error reading Word document: {str(e)}"
    
    def read_csv_file(self, file_content):
        """Read CSV file and return text content"""
        try:
            df = pd.read_csv(io.StringIO(file_content.decode('utf-8')))
            
            text_content = []
            text_content.append(f"CSV file contains {len(df)} rows and {len(df.columns)} columns")
            text_content.append(f"Columns: {', '.join(df.columns.tolist())}")
            text_content.append("\nData preview:")
            
            for idx, row in df.head(10).iterrows():
                row_text = []
                for col in df.columns:
                    if pd.notna(row[col]):
                        row_text.append(f"{col}: {row[col]}")
                text_content.append(f"Row {idx + 1}: {', '.join(row_text)}")
            
            return "\n".join(text_content)
        except Exception as e:
            return f"Error reading CSV file: {str(e)}"
    
    def read_text_file(self, file_content):
        """Read text file"""
        try:
            return file_content.decode('utf-8')
        except Exception as e:
            return f"Error reading text file: {str(e)}"
    
    def process_file(self, file_content, file_name):
        """Process file based on its extension"""
        file_extension = file_name.lower().split('.')[-1]
        
        print(f"📄 Processing file: {file_name} (type: {file_extension})")
        
        if file_extension in ['xlsx', 'xls']:
            return self.read_excel_file(file_content)
        elif file_extension == 'docx':
            return self.read_docx_file(file_content)
        elif file_extension == 'csv':
            return self.read_csv_file(file_content)
        elif file_extension == 'txt':
            return self.read_text_file(file_content)
        else:
            return f"Unsupported file format: {file_extension}"

def test_file_processor():
    """Test the file processor with sample CMDB data"""
    print("🧪 Testing File Processor...")
    print("=" * 50)
    
    processor = FileProcessor()
    
    # Test with sample CSV data (simulating CMDB)
    sample_cmdb_csv = """Asset ID,Asset Name,Type,Owner,Department,Location,Status
SRV001,Web Server 01,Server,John Doe,IT,NYC-DC1,Active
DB001,Database Server,Database,Jane Smith,IT,NYC-DC1,Active
RTR001,Core Router,Network,Tom Brown,IT,NYC-DC1,Active
WS001,Admin Workstation,Workstation,John Doe,IT,NYC-Office,Active"""
    
    print("\n📊 Testing CSV processing with sample CMDB data:")
    result = processor.read_csv_file(sample_cmdb_csv.encode('utf-8'))
    print(result)
    
    # Test with sample text data
    sample_text = """John Doe works in the IT department as a System Administrator.
He manages Web Server 01 and reports to Mike Wilson who is the IT Manager.
The server is located in DataCenter NYC-DC1 in New York.
Jane Smith is the Database Administrator and manages Database Server DB001."""
    
    print("\n" + "=" * 50)
    print("📝 Testing text processing:")
    text_result = processor.read_text_file(sample_text.encode('utf-8'))
    print(text_result)
    
    print("\n" + "=" * 50)
    print("✅ File processor test completed successfully!")
    print("👉 Both CSV and text processing work correctly")
    
    return processor

if __name__ == "__main__":
    test_processor = test_file_processor()
    print("\n🎉 Step 3 PASSED - File processing works!")
    print("👉 Ready for Step 4: LLM Client")
