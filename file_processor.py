#!/usr/bin/env python3
"""
Step 2: Test if all required packages are installed correctly
Run: python test_imports.py
"""

def test_imports():
    """Test if all required packages are installed"""
    print("Testing imports...")
    
    try:
        import streamlit
        print("✓ Streamlit imported successfully")
    except ImportError as e:
        print(f"✗ Streamlit import failed: {e}")
        return False
    
    try:
        import pyvis
        print("✓ Pyvis imported successfully")
    except ImportError as e:
        print(f"✗ Pyvis import failed: {e}")
        return False
    
    try:
        import pandas
        print("✓ Pandas imported successfully")
    except ImportError as e:
        print(f"✗ Pandas import failed: {e}")
        return False
    
    try:
        from docx import Document
        print("✓ Python-docx imported successfully")
    except ImportError as e:
        print(f"✗ Python-docx import failed: {e}")
        return False
    
    try:
        import openpyxl
        print("✓ Openpyxl imported successfully")
    except ImportError as e:
        print(f"✗ Openpyxl import failed: {e}")
        return False
    
    try:
        import requests
        print("✓ Requests imported successfully")
    except ImportError as e:
        print(f"✗ Requests import failed: {e}")
        return False
    
    try:
        import networkx
        print("✓ NetworkX imported successfully")
    except ImportError as e:
        print(f"✗ NetworkX import failed: {e}")
        return False
    
    print("\n🎉 All imports successful! Ready to proceed to next step.")
    return True

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("\n✅ Step 2 PASSED - All packages installed correctly!")
        print("👉 Ready for Step 3: File Processing")
    else:
        print("\n❌ Step 2 FAILED - Please install missing packages:")
        print("   pip install -r requirements.txt")
