#!/usr/bin/env python
"""
Entry point script for running the nightly price analysis web UI.
"""
import sys
import logging
import subprocess
import os

def main():
    """Main function to run the web UI."""
    try:
        # Import streamlit here to check if it's installed
        import streamlit
        
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Build the command to run streamlit
        streamlit_cmd = [
            "streamlit", "run", 
            os.path.join(script_dir, "web_ui.py"),
            "--server.port=8502",
            "--server.address=localhost"
        ]
        
        # Print information
        print("Starting Nightly Price Analysis Web UI...")
        print("URL: http://localhost:8502")
        print("Press Ctrl+C to stop the server")
        
        # Run the streamlit command
        subprocess.run(streamlit_cmd)
        
    except ImportError:
        print("Error: Streamlit is not installed. Please install it with 'pip install streamlit'")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error running web UI: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
