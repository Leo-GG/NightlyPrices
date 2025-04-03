"""
Database connector module for handling database connections and data retrieval.
"""
import os
import logging
import urllib.parse
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure module logger
logger = logging.getLogger(__name__)


class DatabaseConnector:
    """Class to handle database connection and data retrieval."""
    
    def __init__(
        self,
        host: Optional[str] = None,
        db_name: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        port: str = '3306'
    ):
        """
        Initialize the database connector.
        
        Args:
            host: Database host URL
            db_name: Database name
            username: Database username
            password: Database password
            port: Database port
        """
        # Use provided parameters or get from environment variables
        self.host = host or os.getenv('DB_HOST')
        self.db_name = db_name or os.getenv('DB_NAME')
        self.username = username or os.getenv('DB_USERNAME')  # Updated from DB_USER to DB_USERNAME
        self.password = password or os.getenv('DB_PASSWORD')
        self.port = port or os.getenv('DB_PORT', '3306')
        self.engine = None
        
        # Print connection info (without password)
        logger.info(f"Connecting to database: {self.db_name} on {self.host}:{self.port} as {self.username}")
    
    def get_connection_string(self) -> str:
        """
        Create and return a properly formatted connection string.
        
        Returns:
            Database connection string
        """
        # Extract the hostname from the URL without protocol
        if self.host and self.host.startswith(('http://', 'https://')):
            hostname = self.host.split('://')[-1]
            logger.info(f"Cleaned host: {hostname}")
        else:
            hostname = self.host
        
        # URL encode the password to handle special characters
        password_encoded = urllib.parse.quote_plus(self.password) if self.password else ""
        
        # Create SQLAlchemy connection string
        return f"mysql+pymysql://{self.username}:{password_encoded}@{hostname}:{self.port}/{self.db_name}"
    
    def connect(self, timeout: int = 10) -> bool:
        """
        Establish a connection to the database.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            connection_string = self.get_connection_string()
            
            # Create SQLAlchemy engine
            self.engine = create_engine(connection_string, connect_args={'connect_timeout': timeout})
            
            # Test the connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                value = result.scalar()
                logger.info(f"Database connection test result: {value}")
            
            logger.info("Database connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            
            # Check for common connection issues
            if "timeout" in str(e).lower():
                logger.error("Connection timed out. Possible reasons:")
                logger.error("  - Database server is not running")
                logger.error("  - Firewall is blocking the connection")
                logger.error("  - Incorrect host or port")
                logger.error("  - VPN or network issues")
            elif "authentication" in str(e).lower():
                logger.error("Authentication failed. Possible reasons:")
                logger.error("  - Incorrect username or password")
                logger.error("  - User does not have access to the database")
            
            return False
    
    def fetch_data(self, query: str) -> Optional[pd.DataFrame]:
        """
        Fetch data from the database using the provided query.
        
        Args:
            query: SQL query to execute
            
        Returns:
            DataFrame containing the fetched data, or None if the query fails
        """
        if self.engine is None:
            if not self.connect():
                logger.error("Cannot fetch data - database connection failed")
                return None
        
        try:
            logger.info(f"Executing query: {query}")
            df = pd.read_sql(query, self.engine)
            logger.info(f"Fetched {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            return None


def get_db_connection() -> Optional[create_engine]:
    """
    Create a database connection using SQLAlchemy with credentials from the .env file.
    
    Returns:
        SQLAlchemy engine object or None if connection fails
    """
    db_connector = DatabaseConnector()
    if db_connector.connect():
        return db_connector.engine
    return None


def test_db_connection() -> dict:
    """
    Test the database connection and provide detailed error information.
    
    Returns:
        Dictionary with connection status and error information
    """
    logger.info("Testing database connection...")
    
    # Initialize database connector
    db_connector = DatabaseConnector()
    
    # Test connection
    success = db_connector.connect()
    
    result = {
        "success": success,
        "engine": db_connector.engine if success else None
    }
    
    return result
