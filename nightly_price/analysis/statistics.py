"""
Statistics module for analyzing price data patterns and generating summary statistics.
"""
import logging
import pandas as pd
from typing import Dict, Any

# Configure module logger
logger = logging.getLogger(__name__)


class PriceAnalyzer:
    """Class for analyzing price data and generating statistics."""
    
    def __init__(self):
        """Initialize the price analyzer."""
        pass
    
    def generate_summary_statistics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate summary statistics for the price data.
        
        Args:
            df: Dataframe with price data
            
        Returns:
            Summary statistics dataframe
        """
        logger.info("Generating summary statistics...")
        
        # Identify available columns for statistics
        available_columns = {}
        
        if 'base' in df.columns and not df['base'].isnull().all():
            available_columns['base'] = 'mean'
        
        for col in ['seasonality', 'dow', 'event']:
            if col in df.columns and not df[col].isnull().all():
                available_columns[col] = ['mean', 'min', 'max']
        
        if 'price' in df.columns:
            available_columns['price'] = ['mean', 'min', 'max', 'std']
        
        if 'total_price' in df.columns:
            available_columns['total_price'] = ['mean', 'min', 'max', 'std']
        
        # Group by multiunit_id and calculate statistics
        summary = df.groupby('multiunit_id').agg(available_columns).reset_index()
        
        # Flatten the multi-level column names
        summary.columns = ['_'.join(col).strip('_') for col in summary.columns.values]
        
        return summary
    
    def analyze_event_patterns(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Analyze patterns in price data across properties.
        
        Args:
            df: Dataframe with price data
            
        Returns:
            Dictionary of dataframes with different analyses
        """
        logger.info("Analyzing price patterns...")
        
        # Since we don't have event data in our actual data structure,
        # we'll analyze price variations by day of week and month instead
        
        # Add day of week and month columns
        df_copy = df.copy()
        df_copy['day_of_week'] = df_copy['date'].dt.day_name()
        df_copy['month'] = df_copy['date'].dt.month_name()
        
        # Analyze price by day of week
        dow_analysis = df_copy.groupby(['multiunit_id', 'day_of_week'])['price'].agg(['mean', 'std', 'count']).reset_index()
        
        # Analyze price by month
        month_analysis = df_copy.groupby(['multiunit_id', 'month'])['price'].agg(['mean', 'std', 'count']).reset_index()
        
        # Identify high-price periods (top 10% of prices for each property)
        high_price_threshold = df_copy.groupby('multiunit_id')['price'].quantile(0.9).reset_index()
        high_price_threshold.columns = ['multiunit_id', 'high_price_threshold']
        
        # Merge the threshold back to the main dataframe
        df_copy = pd.merge(df_copy, high_price_threshold, on='multiunit_id')
        
        # Flag high price dates
        df_copy['is_high_price'] = df_copy['price'] >= df_copy['high_price_threshold']
        
        # Count high price days by month and day of week
        high_price_by_month = df_copy[df_copy['is_high_price']].groupby(['multiunit_id', 'month']).size().reset_index(name='high_price_count')
        high_price_by_dow = df_copy[df_copy['is_high_price']].groupby(['multiunit_id', 'day_of_week']).size().reset_index(name='high_price_count')
        
        # Return a dictionary of dataframes for different analyses
        return {
            'dow_analysis': dow_analysis,
            'month_analysis': month_analysis,
            'high_price_by_month': high_price_by_month,
            'high_price_by_dow': high_price_by_dow
        }
    
    def detect_seasonal_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect seasonal patterns in the price data.
        
        Args:
            df: Dataframe with price data
            
        Returns:
            Dataframe with seasonal pattern information
        """
        logger.info("Detecting seasonal patterns...")
        
        # Add month and quarter columns
        df_copy = df.copy()
        df_copy['month'] = df_copy['date'].dt.month
        df_copy['quarter'] = df_copy['date'].dt.quarter
        
        # Calculate monthly averages
        monthly_avg = df_copy.groupby(['multiunit_id', 'month'])['price'].mean().reset_index()
        
        # Calculate quarterly averages
        quarterly_avg = df_copy.groupby(['multiunit_id', 'quarter'])['price'].mean().reset_index()
        
        # Calculate overall average for each property
        property_avg = df_copy.groupby('multiunit_id')['price'].mean().reset_index()
        property_avg.columns = ['multiunit_id', 'avg_price']
        
        # Merge monthly averages with property averages
        monthly_patterns = pd.merge(monthly_avg, property_avg, on='multiunit_id')
        
        # Calculate seasonal index (ratio of monthly average to overall average)
        monthly_patterns['seasonal_index'] = monthly_patterns['price'] / monthly_patterns['avg_price']
        
        # Identify peak and low seasons
        monthly_patterns['is_peak_season'] = monthly_patterns['seasonal_index'] > 1.1  # 10% above average
        monthly_patterns['is_low_season'] = monthly_patterns['seasonal_index'] < 0.9   # 10% below average
        
        return monthly_patterns
