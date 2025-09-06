#!/usr/bin/env python3
"""
NxTrix CRM - Main Application Entry Point
This file serves as the entry point for Streamlit Cloud deployment.
It redirects to the actual app in the /crm/ directory.
"""

import os
import sys

# Add the CRM directory to the Python path
crm_path = os.path.join(os.path.dirname(__file__), 'crm')
sys.path.insert(0, crm_path)

# Change working directory to CRM folder
os.chdir(crm_path)

# Import and run the main CRM application
try:
    # Import the main app from the crm directory
    import importlib.util
    
    app_path = os.path.join(crm_path, 'app.py')
    spec = importlib.util.spec_from_file_location("crm_app", app_path)
    crm_app = importlib.util.module_from_spec(spec)
    
    # Execute the CRM app
    spec.loader.exec_module(crm_app)
    
except Exception as e:
    import streamlit as st
    
    st.error(f"""
    ## 🚨 Application Loading Error
    
    There was an error loading the NxTrix CRM application:
    
    ```
    {str(e)}
    ```
    
    **Troubleshooting Steps:**
    1. Ensure all dependencies are installed
    2. Check that environment variables are properly configured
    3. Verify the CRM application files are present
    
    **Contact Support:** If this error persists, please contact the development team.
    """)
    
    st.stop()
