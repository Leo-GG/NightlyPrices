"""
Main application module for nightly price analysis.
"""
import os
import sys
import logging
import argparse
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_analysis(args):
    """
    Run the nightly price analysis in command-line mode.
    
    Args:
        args: Command line arguments
    """
    try:
        # Import the main function from the nightly_price package
        from nightly_price.analysis import NightlyPriceAnalysis
        
        # Initialize and run analysis with the provided arguments
        analysis = NightlyPriceAnalysis(
            output_dir=args.output_dir,
            cache_dir=args.cache_dir,
            use_cached_data=not args.no_cache,
            force_fallback=args.fallback
        )
        
        # Run the analysis with robust error handling for database connection issues
        try:
            results = analysis.run()
            logger.info("Analysis completed successfully!")
            return results
        except Exception as e:
            logger.error(f"Error during analysis execution: {e}")
            logger.info("Attempting to continue with fallback data...")
            
            # Try again with fallback data if the first attempt failed
            try:
                analysis.force_fallback = True
                results = analysis.run()
                logger.info("Analysis completed with fallback data!")
                return results
            except Exception as e2:
                logger.error(f"Error during fallback analysis: {e2}")
                raise
                
    except ImportError as e:
        logger.error(f"Error importing nightly_price package: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running analysis: {e}", exc_info=True)
        sys.exit(1)

def run_web_ui():
    """Run the nightly price analysis web UI."""
    try:
        # Check if streamlit is installed
        try:
            import streamlit
        except ImportError:
            logger.error("Streamlit is not installed. Please install it with 'pip install streamlit'")
            sys.exit(1)
        
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Build the command to run streamlit
        streamlit_cmd = [
            "streamlit", "run", 
            os.path.join(script_dir, "web_ui.py"),
            "--server.port=8501",
            "--server.address=localhost"
        ]
        
        # Print information
        logger.info("Starting Nightly Price Analysis Web UI...")
        logger.info("URL: http://localhost:8501")
        logger.info("Press Ctrl+C to stop the server")
        
        # Run the streamlit command
        subprocess.run(streamlit_cmd)
        
    except Exception as e:
        logger.error(f"Error running web UI: {e}", exc_info=True)
        sys.exit(1)

def main():
    """Main function to parse arguments and run the appropriate mode."""
    parser = argparse.ArgumentParser(description='Nightly Price Analysis')
    
    # Add subparsers for different modes
    subparsers = parser.add_subparsers(dest='mode', help='Mode to run')
    
    # Analysis mode parser
    analysis_parser = subparsers.add_parser('analysis', help='Run analysis in command-line mode')
    analysis_parser.add_argument('--fetch', action='store_true', help='Force fetch data from database')
    analysis_parser.add_argument('--no-cache', action='store_true', help='Do not use cached data')
    analysis_parser.add_argument('--fallback', action='store_true', help='Force using fallback data')
    analysis_parser.add_argument('--output-dir', type=str, default='output', help='Output directory')
    analysis_parser.add_argument('--cache-dir', type=str, default='data', help='Cache directory')
    
    # Web UI mode parser
    web_parser = subparsers.add_parser('web', help='Run web UI')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the appropriate mode
    if args.mode == 'analysis':
        run_analysis(args)
    elif args.mode == 'web':
        run_web_ui()
    else:
        # Default to web UI if no mode specified
        logger.info("No mode specified, defaulting to web UI")
        run_web_ui()

if __name__ == "__main__":
    main()
