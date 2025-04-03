"""
Data fetching and caching module for nightly price data.
"""
import os
import logging
import pandas as pd
from typing import List, Optional

from nightly_price.database.connector import DatabaseConnector

# Configure module logger
logger = logging.getLogger(__name__)

# Define multiunit IDs from the requirements
MULTIUNIT_IDS = [
    '2789103', '3134165', '3134168', '3482048', '3592887', '3603346', '3739908',
    '3824642', '3824643', '3867371', '3867385'
]


class PriceDataManager:
    """Class to manage nightly price data fetching and caching."""
    
    def __init__(self, cache_dir: str = 'data'):
        """
        Initialize the price data manager.
        
        Args:
            cache_dir: Directory to store cached data
        """
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, 'nightly_prices_original.csv')
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def fetch_nightly_prices(self, multiunit_ids: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Fetch nightly price data from the database.
        
        Args:
            multiunit_ids: List of multiunit IDs to fetch data for, defaults to MULTIUNIT_IDS
            
        Returns:
            pandas.DataFrame: Nightly price data
        """
        if multiunit_ids is None:
            multiunit_ids = MULTIUNIT_IDS
            
        try:
            # Initialize database connector
            db_connector = DatabaseConnector()
            
            # Test connection
            if not db_connector.connect():
                logger.warning("Database connection failed, falling back to cached data")
                return self.read_cached_data()
            
            # Build the SQL query
            multiunit_ids_str = "'" + "','".join(multiunit_ids) + "'"
            query = f"""
            SELECT 
                multiunit_id, 
                date, 
                base, 
                seasonality, 
                dow, 
                event, 
                price
            FROM 
                nightly_prices
            WHERE 
                multiunit_id IN ({multiunit_ids_str});
            """
            
            # Execute the query
            logger.info("Fetching nightly price data from database...")
            df = db_connector.fetch_data(query)
            
            if df is None or df.empty:
                logger.warning("No data returned from database, falling back to cached data")
                return self.read_cached_data()
            
            # Convert date column to datetime
            df['date'] = pd.to_datetime(df['date'])
            
            # Print data summary
            logger.info(f"Fetched {len(df)} rows of nightly price data")
            logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
            logger.info(f"Number of unique multiunit_ids: {df['multiunit_id'].nunique()}")
            
            # Save the fetched data to a CSV file
            self.save_to_cache(df)
            
            return df
        
        except Exception as e:
            logger.error(f"Error fetching data from database: {e}")
            logger.warning("Falling back to cached data...")
            return self.read_cached_data()
    
    def save_to_cache(self, df: pd.DataFrame) -> None:
        """
        Save data to cache file.
        
        Args:
            df: DataFrame to save
        """
        try:
            df.to_csv(self.cache_file, index=False)
            logger.info(f"Saved original data to {self.cache_file}")
        except Exception as e:
            logger.error(f"Error saving data to cache: {e}")
    
    def read_cached_data(self) -> pd.DataFrame:
        """
        Read nightly price data from the cached CSV file.
        
        Returns:
            pandas.DataFrame: Nightly price data
        
        Raises:
            FileNotFoundError: If cache file doesn't exist
        """
        if os.path.exists(self.cache_file):
            logger.info(f"Reading cached data from {self.cache_file}...")
            df = pd.read_csv(self.cache_file)
            
            # Convert date column to datetime
            df['date'] = pd.to_datetime(df['date'])
            
            # Print data summary
            logger.info(f"Loaded {len(df)} rows of nightly price data")
            logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
            logger.info(f"Number of unique multiunit_ids: {df['multiunit_id'].nunique()}")
            
            return df
        else:
            logger.error(f"No cached data found at {self.cache_file}")
            raise FileNotFoundError(
                f"No cached data found at {self.cache_file}. Please run with database connection first."
            )
