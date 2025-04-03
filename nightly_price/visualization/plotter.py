"""
Plotter module for creating visualizations of price data.
"""
import os
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, List

# Configure module logger
logger = logging.getLogger(__name__)


class PricePlotter:
    """Class for creating visualizations of price data."""
    
    def __init__(self, output_dir: str = 'plots'):
        """
        Initialize the price plotter.
        
        Args:
            output_dir: Directory to save plots
        """
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def plot_price_trends(self, df: pd.DataFrame, multiunit_ids: Optional[List[str]] = None) -> None:
        """
        Create visualizations of price trends.
        
        Args:
            df: Dataframe with price data
            multiunit_ids: List of multiunit IDs to plot, if None, will sample a few
        """
        logger.info(f"Creating visualizations in '{self.output_dir}' directory...")
        
        # If no multiunit_ids provided, sample a few
        if multiunit_ids is None:
            multiunit_ids = np.random.choice(
                df['multiunit_id'].unique().tolist(), 
                min(3, len(df['multiunit_id'].unique()))
            )
        
        for multiunit_id in multiunit_ids:
            unit_data = df[df['multiunit_id'] == multiunit_id]
            
            # Plot total price over time
            plt.figure(figsize=(12, 6))
            plt.plot(unit_data['date'], unit_data['total_price'])
            plt.title(f'Total Price for Property {multiunit_id}')
            plt.xlabel('Date')
            plt.ylabel('Price ($)')
            plt.grid(True)
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/total_price_{multiunit_id}.png')
            plt.close()
            
            # Check if we have the factor columns
            factor_columns = ['base', 'seasonality', 'dow', 'event']
            has_factors = all(col in unit_data.columns for col in factor_columns) and not unit_data[factor_columns].isnull().all().any()
            
            if has_factors:
                # Plot components (seasonality, dow, event) over time
                fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
                
                axes[0].plot(unit_data['date'], unit_data['seasonality'])
                axes[0].set_title('Seasonality Factor')
                axes[0].grid(True)
                
                axes[1].plot(unit_data['date'], unit_data['dow'])
                axes[1].set_title('Day of Week Factor')
                axes[1].grid(True)
                
                axes[2].plot(unit_data['date'], unit_data['event'])
                axes[2].set_title('Event Factor')
                axes[2].grid(True)
                
                plt.tight_layout()
                plt.savefig(f'{self.output_dir}/factors_{multiunit_id}.png')
                plt.close()
                
                # Plot base price over time
                plt.figure(figsize=(12, 6))
                plt.plot(unit_data['date'], unit_data['base'])
                plt.title(f'Base Price for Property {multiunit_id}')
                plt.xlabel('Date')
                plt.ylabel('Base Price ($)')
                plt.grid(True)
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(f'{self.output_dir}/base_price_{multiunit_id}.png')
                plt.close()
        
        logger.info(f"Created visualizations for {len(multiunit_ids)} properties")
    
    def plot_seasonal_patterns(self, df: pd.DataFrame) -> None:
        """
        Create visualizations of seasonal patterns.
        
        Args:
            df: Dataframe with price data
        """
        logger.info("Creating seasonal pattern visualizations...")
        
        # Add month column if not already present
        if 'month' not in df.columns:
            df = df.copy()
            df['month'] = df['date'].dt.month
            df['month_name'] = df['date'].dt.month_name()
        
        # Calculate monthly averages
        monthly_avg = df.groupby(['multiunit_id', 'month'])['price'].mean().reset_index()
        
        # Sample a few multiunit_ids to plot
        sample_ids = np.random.choice(
            monthly_avg['multiunit_id'].unique().tolist(),
            min(3, len(monthly_avg['multiunit_id'].unique()))
        )
        
        # Create a bar chart for each sampled property
        for multiunit_id in sample_ids:
            property_data = monthly_avg[monthly_avg['multiunit_id'] == multiunit_id]
            
            plt.figure(figsize=(12, 6))
            plt.bar(property_data['month'], property_data['price'])
            plt.title(f'Monthly Average Prices for Property {multiunit_id}')
            plt.xlabel('Month')
            plt.ylabel('Average Price ($)')
            plt.grid(True, axis='y')
            plt.xticks(range(1, 13), ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/monthly_avg_{multiunit_id}.png')
            plt.close()
        
        logger.info(f"Created seasonal pattern visualizations for {len(sample_ids)} properties")
    
    def plot_weekday_patterns(self, df: pd.DataFrame) -> None:
        """
        Create visualizations of weekday patterns.
        
        Args:
            df: Dataframe with price data
        """
        logger.info("Creating weekday pattern visualizations...")
        
        # Add day of week column if not already present
        if 'day_of_week' not in df.columns:
            df = df.copy()
            df['day_of_week'] = df['date'].dt.dayofweek
            df['day_name'] = df['date'].dt.day_name()
        
        # Calculate day of week averages
        dow_avg = df.groupby(['multiunit_id', 'day_of_week'])['price'].mean().reset_index()
        
        # Sample a few multiunit_ids to plot
        sample_ids = np.random.choice(
            dow_avg['multiunit_id'].unique().tolist(),
            min(3, len(dow_avg['multiunit_id'].unique()))
        )
        
        # Create a bar chart for each sampled property
        for multiunit_id in sample_ids:
            property_data = dow_avg[dow_avg['multiunit_id'] == multiunit_id]
            
            plt.figure(figsize=(10, 6))
            plt.bar(property_data['day_of_week'], property_data['price'])
            plt.title(f'Day of Week Average Prices for Property {multiunit_id}')
            plt.xlabel('Day of Week')
            plt.ylabel('Average Price ($)')
            plt.grid(True, axis='y')
            plt.xticks(range(7), ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/dow_avg_{multiunit_id}.png')
            plt.close()
        
        logger.info(f"Created weekday pattern visualizations for {len(sample_ids)} properties")
    
    def plot_price_distribution(self, df: pd.DataFrame) -> None:
        """
        Create visualizations of price distributions.
        
        Args:
            df: Dataframe with price data
        """
        logger.info("Creating price distribution visualizations...")
        
        # Sample a few multiunit_ids to plot
        sample_ids = np.random.choice(
            df['multiunit_id'].unique().tolist(),
            min(3, len(df['multiunit_id'].unique()))
        )
        
        # Create a histogram for each sampled property
        for multiunit_id in sample_ids:
            property_data = df[df['multiunit_id'] == multiunit_id]
            
            plt.figure(figsize=(10, 6))
            plt.hist(property_data['price'], bins=20, alpha=0.7)
            plt.title(f'Price Distribution for Property {multiunit_id}')
            plt.xlabel('Price ($)')
            plt.ylabel('Frequency')
            plt.grid(True)
            plt.tight_layout()
            plt.savefig(f'{self.output_dir}/price_dist_{multiunit_id}.png')
            plt.close()
        
        logger.info(f"Created price distribution visualizations for {len(sample_ids)} properties")
