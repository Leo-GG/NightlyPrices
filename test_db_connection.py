import os
import sys
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import time
import urllib.parse
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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
        self.username = username or os.getenv('DB_USERNAME')
        self.password = password or os.getenv('DB_PASSWORD')
        self.port = port or os.getenv('DB_PORT', '3306')
        self.engine = None
        
        # Print connection parameters (without password)
        logger.info(f"Connection parameters:")
        logger.info(f"  Host: {self.host}")
        logger.info(f"  Database: {self.db_name}")
        logger.info(f"  User: {self.username}")
        logger.info(f"  Port: {self.port}")
        
        # Check if any parameters are missing
        missing_params = []
        if not self.host:
            missing_params.append("DB_HOST")
        if not self.db_name:
            missing_params.append("DB_NAME")
        if not self.username:
            missing_params.append("DB_USERNAME")
        if not self.password:
            missing_params.append("DB_PASSWORD")
        
        if missing_params:
            error_msg = f"Missing database parameters: {', '.join(missing_params)}"
            logger.error(error_msg)
            print(f"ERROR: {error_msg}")
            print("Please check your .env file and ensure all required variables are set.")
    
    def get_connection_string(self) -> str:
        """
        Create and return a properly formatted connection string.
        
        Returns:
            Database connection string
        """
        # Extract the hostname from the URL without protocol
        if self.host.startswith(("http://", "https://")):
            hostname = self.host.split("://")[-1]
            logger.info(f"  Cleaned Host: {hostname}")
        else:
            hostname = self.host
        
        # Create database connection with properly escaped password
        password_encoded = urllib.parse.quote_plus(self.password) if self.password else ""
        logger.info("Password URL-encoded for special characters")
        
        return f"mysql+pymysql://{self.username}:{password_encoded}@{hostname}:{self.port}/{self.db_name}"
    
    def connect(self, timeout: int = 5) -> bool:
        """
        Establish a connection to the database.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            connection_string = self.get_connection_string()
            logger.info(f"Connection string (without password): mysql+pymysql://{self.username}:***@{self.host}:{self.port}/{self.db_name}")
            
            logger.info("Creating SQLAlchemy engine...")
            self.engine = create_engine(
                connection_string, 
                connect_args={'connect_timeout': timeout},
                echo=False  # Don't show SQL queries to avoid leaking credentials
            )
            
            # Test connection with a simple query
            logger.info("Testing connection with a simple query...")
            start_time = time.time()
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                value = result.scalar()
                logger.info(f"Query result: {value}")
            
            end_time = time.time()
            logger.info(f"Connection and query completed in {end_time - start_time:.2f} seconds")
            logger.info("Database connection successful!")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
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
            elif "database" in str(e).lower() and "not exist" in str(e).lower():
                logger.error("Database does not exist. Possible reasons:")
                logger.error("  - Incorrect database name")
                logger.error("  - Database has not been created")
            elif "translate host" in str(e).lower():
                logger.error("Hostname resolution error. Possible reasons:")
                logger.error("  - Special characters in password need URL encoding")
                logger.error("  - Invalid hostname format")
            
            return False
    
    def test_pymysql_connection(self, timeout: int = 5) -> bool:
        """
        Test the database connection using PyMySQL directly.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            # Extract the hostname from the URL without protocol
            if self.host.startswith(("http://", "https://")):
                hostname = self.host.split("://")[-1]
            else:
                hostname = self.host
            
            import pymysql
            logger.info("\nTesting connection with PyMySQL...")
            
            # URL encode the password to handle special characters
            password_encoded = self.password
            
            # Create connection
            conn = pymysql.connect(
                host=hostname,
                user=self.username,
                password=password_encoded,
                database=self.db_name,
                port=int(self.port),
                connect_timeout=timeout
            )
            
            # Test connection with a simple query
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                logger.info(f"Query result: {result}")
            
            # Close connection
            conn.close()
            
            logger.info("PyMySQL connection successful!")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting with PyMySQL: {str(e)}")
            return False

def test_db_connection() -> bool:
    """
    Test the database connection using the DatabaseConnector class.
    
    Returns:
        True if connection was successful, False otherwise
    """
    print("\n=== Database Connection Test ===\n")
    
    # Create database connector
    db_connector = DatabaseConnector()
    
    # Test SQLAlchemy connection
    sqlalchemy_result = db_connector.connect()
    print(f"SQLAlchemy connection: {'SUCCESS' if sqlalchemy_result else 'FAILED'}")
    
    # Test PyMySQL connection
    pymysql_result = db_connector.test_pymysql_connection()
    print(f"PyMySQL connection: {'SUCCESS' if pymysql_result else 'FAILED'}")
    
    # Return overall result
    return sqlalchemy_result and pymysql_result


if __name__ == "__main__":
    success = test_db_connection()
    # Exit with appropriate code
    sys.exit(0 if success else 1)
