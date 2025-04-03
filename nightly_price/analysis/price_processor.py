"""
Price processor module for extrapolating prices and finding improved matches.
"""
import logging
import pandas as pd
import numpy as np
from datetime import timedelta
from typing import Dict, Any

# Configure module logger
logger = logging.getLogger(__name__)


class PriceProcessor:
    """Class for processing nightly price data."""
    
    def __init__(self):
        """Initialize the price processor."""
        pass
    
    def extrapolate_prices_backward(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extrapolate prices back to January 1, 2024 based on the requirements.
        
        Args:
            df: Original nightly price data
            
        Returns:
            Combined dataframe with original and extrapolated data
        """
        logger.info("Extrapolating prices back to January 1, 2024...")
        
        # Convert date to datetime if it's not already
        if df['date'].dtype == 'object':
            df['date'] = pd.to_datetime(df['date'])
        
        # Get the earliest date in the data
        earliest_date = df['date'].min()
        
        # Define the target start date (January 1, 2024)
        target_start_date = pd.Timestamp('2024-01-01')
        
        # If earliest date is already before or equal to target, no need to extrapolate
        if earliest_date <= target_start_date:
            logger.info("Data already starts before or on January 1, 2024. No extrapolation needed.")
            return df
        
        # Create a list to store extrapolated data
        extrapolated_data = []
        
        # Get unique multiunit_ids
        unique_multiunit_ids = df['multiunit_id'].unique()
        
        # For each multiunit_id, extrapolate prices backward
        for multiunit_id in unique_multiunit_ids:
            # Get data for this multiunit_id
            group = df[df['multiunit_id'] == multiunit_id].copy()
            
            # Sort by date
            group = group.sort_values('date')
            
            # Get the earliest date for this multiunit_id
            group_earliest_date = group['date'].min()
            
            # Create a date range from target start date to the day before the earliest date
            if group_earliest_date > target_start_date:
                missing_dates = pd.date_range(start=target_start_date, end=group_earliest_date - pd.Timedelta(days=1))
                
                # For each missing date, find the corresponding date one year later
                for missing_date in missing_dates:
                    # Find the date one year later
                    future_date = missing_date + pd.DateOffset(years=1)
                    
                    # Create a new row for the extrapolated data
                    new_row = {
                        'multiunit_id': multiunit_id,
                        'date': missing_date,
                        'is_extrapolated': True
                    }
                    
                    # 1. Copy event factor from date+1 year
                    exact_future_match = group[group['date'] == future_date]
                    if not exact_future_match.empty and 'event' in exact_future_match.columns:
                        new_row['event'] = exact_future_match.iloc[0]['event']
                    
                    # 2. Copy seasonality from date+1 year
                    if not exact_future_match.empty and 'seasonality' in exact_future_match.columns:
                        new_row['seasonality'] = exact_future_match.iloc[0]['seasonality']
                    # 3. Copy over base factor if it exists
                    if not exact_future_match.empty and 'base' in exact_future_match.columns:
                        new_row['base'] = exact_future_match.iloc[0]['base']

                    # 4. Find matching days of the week in +1 year dates for dow factor
                    same_weekday_dates = group[
                        (group['date'].dt.dayofweek == future_date.dayofweek) & 
                        (group['date'] >= future_date - pd.Timedelta(days=14)) & 
                        (group['date'] <= future_date + pd.Timedelta(days=14))
                    ]
                    
                    if not same_weekday_dates.empty and 'dow' in same_weekday_dates.columns:
                        try:
                            # 5. If there are two matching days of the week, use the average of their dow factors
                            if len(same_weekday_dates) >= 2:
                                new_row['dow'] = same_weekday_dates['dow'].mean()
                            else:
                                # Find the closest date with the same weekday
                                closest_idx = (same_weekday_dates['date'] - future_date).abs().idxmin()
                                closest_date = same_weekday_dates.loc[closest_idx]
                                new_row['dow'] = closest_date['dow']
                            # Calculate price if all necessary factors are present
                            if all(k in new_row for k in ['base', 'seasonality', 'dow', 'event']):
                                new_row['price'] = (new_row['base'] + new_row['seasonality'] + 
                                                    new_row['dow'] + new_row['event'] )* 0.97  # 3% less for previous year
                            elif 'price' in closest_date and not pd.isna(closest_date['price']):
                                # Fall back to copying price directly if factors are missing
                                new_row['price'] = closest_date['price'] * 0.97  # 3% less for previous year
                            
                            extrapolated_data.append(new_row)
                        except (KeyError, ValueError) as e:
                            # Log the error and continue with the next date
                            logger.warning(f"Error processing date {missing_date}: {e}")
        
        # Convert extrapolated data to DataFrame
        if extrapolated_data:
            extrapolated_df = pd.DataFrame(extrapolated_data)
            
            # Combine original and extrapolated data
            combined_df = pd.concat([df, extrapolated_df], ignore_index=True)
            
            # Add is_extrapolated column to original data if it doesn't exist
            if 'is_extrapolated' not in df.columns:
                combined_df.loc[combined_df['is_extrapolated'].isna(), 'is_extrapolated'] = False
            
            # Sort by multiunit_id and date
            combined_df = combined_df.sort_values(['multiunit_id', 'date']).reset_index(drop=True)
            
            logger.info(f"Added {len(extrapolated_data)} extrapolated price points")
            return combined_df
        else:
            # If no extrapolation was done, return the original DataFrame
            logger.info("No extrapolation needed")
            if 'is_extrapolated' not in df.columns:
                df['is_extrapolated'] = False
            return df
    
    def find_improved_matches(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Find improved matches for future dates based on past data.
        
        Args:
            df: Dataframe with price data
            
        Returns:
            Dataframe with improved matches for dates between Jan 1, 2025 and Mar 31, 2026
        """
        logger.info("Finding improved -1 year matches for dates between Jan 1, 2025 and Mar 31, 2026...")
        
        # Convert date to datetime if it's not already
        if df['date'].dtype == 'object':
            df['date'] = pd.to_datetime(df['date'])
        
        # Define the target date range (Jan 1, 2025 to Mar 31, 2026)
        start_date = pd.to_datetime('2025-01-01')
        end_date = pd.to_datetime('2026-03-31')
        past_date_limit = pd.to_datetime('2025-04-21')

        # Filter for dates within the target range
        target_dates = df[(df['date'] >= start_date) & (df['date'] <= end_date)].copy()
        
        # If no target dates, return empty dataframe
        if target_dates.empty:
            logger.warning(f"No dates found between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}. Returning empty dataframe.")
            return pd.DataFrame()
        
        # Filter for past dates (dates before Jan 1, 2025)
        past_data = df[df['date'] < past_date_limit].copy()
        
        # If no past dates, return empty dataframe
        if past_data.empty:
            logger.warning("No past dates found for matching. Returning empty dataframe.")
            return pd.DataFrame()
        
        # Create a list to store improved matches
        improved_matches = []
        
        # Check if 'event' column exists in the dataframe
        has_event_column = 'event' in df.columns
        
        # Group by multiunit_id
        for multiunit_id, future_group in target_dates.groupby('multiunit_id'):
            # Get past data for this multiunit_id
            past_group = past_data[past_data['multiunit_id'] == multiunit_id]
            
            # Skip if no past data for this multiunit_id
            if past_group.empty:
                continue
            
            # For each target date
            for _, future_row in future_group.iterrows():
                future_date = future_row['date']
                
                # Try to find a matching date from exactly 1 year ago
                target_date = future_date - pd.DateOffset(years=1)
                
                # Check if we have the event column and can perform event matching
                best_match_date = None
                match_reason = ""
                
                if has_event_column:
                    future_event = future_row.get('event', 0)
                    
                    # First matching strategy: If future date has an event > 1, match with past dates with same event
                    if future_event is not None and future_event > 1:
                        # Find past dates with the same event within a 14-day window
                        past_event_matches = past_group[
                            (abs(past_group['date'] - target_date) <= pd.Timedelta(days=14)) &
                            (np.abs(past_group['event'] - future_event) <= 20)
                        ]
                        
                        if not past_event_matches.empty:
                            # Get the closest date with the same event
                            min_idx = abs(past_event_matches['date'] - target_date).argmin()
                            best_match_date = past_event_matches.iloc[min_idx]['date']
                            match_reason = "event_match"
                
                # Second matching strategy: If no event match or future date has no event, try day of week matching
                if best_match_date is None:
                    if has_event_column:
                        # If future date has no event, match with past dates that also have no event
                        # future_has_event = future_event is not None and future_event > 1
                        
                        #if not future_has_event:
                        # Find dates with the same weekday within a 14-day window that also have no event
                        past_dow_matches = past_group[
                            (abs(past_group['date'] - target_date) <= pd.Timedelta(days=14)) &
                            (past_group['date'].dt.dayofweek == target_date.dayofweek) &
                            ((past_group['event'].isna()) | (past_group['event'] <= 10))
                        ]
                        
                        if not past_dow_matches.empty:
                            # Get the closest date with the same weekday and no event
                            min_idx = abs(past_dow_matches['date'] - target_date).argmin()
                            best_match_date = past_dow_matches.iloc[min_idx]['date']
                            match_reason = "weekday_match_no_event"
                    
                    # If still no match or no event column, extend search to 3 weeks
                    if best_match_date is None:
                        # Find dates with the same weekday within a 21-day window
                        past_dow_matches = past_group[
                            (abs(past_group['date'] - target_date) <= pd.Timedelta(days=21)) &
                            (past_group['date'].dt.dayofweek == target_date.dayofweek) &
                            ((past_group['event'].isna()) | (past_group['event'] <= 10))
                        ]
                        
                        if not past_dow_matches.empty:
                            # Get the closest date with the same weekday
                            min_idx = abs(past_dow_matches['date'] - target_date).argmin()
                            best_match_date = past_dow_matches.iloc[min_idx]['date']
                            match_reason = "weekday_match"
                
                # If still no match, find the closest date within a 14-day window
                if best_match_date is None:
                    closest_dates = past_group[abs(past_group['date'] - target_date) <= pd.Timedelta(days=14)]
                    if not closest_dates.empty:
                        min_idx = abs(closest_dates['date'] - target_date).argmin()
                        best_match_date = closest_dates.iloc[min_idx]['date']
                        match_reason = "closest_date"
                    else:
                        # Skip if no close match found
                        continue
                
                # Get the matching row
                matching_row = past_group[past_group['date'] == best_match_date].iloc[0]
                days_diff = abs((best_match_date - target_date).days)
                
                # Create a new row for the improved match
                new_row = {
                    'multiunit_id': multiunit_id,
                    'date': future_date,
                    'matched_from': best_match_date,
                    'days_diff': days_diff,
                    'is_improved_match': True,
                    'match_reason': match_reason
                }
                
                # Copy price and calculate adjusted price (with 3% year-over-year growth)
                if 'price' in matching_row:
                    new_row['price'] = matching_row['price'] * 1.03
                
                # Copy factor columns if they exist
                for col in ['base', 'seasonality', 'dow', 'event']:
                    if col in matching_row and not pd.isna(matching_row[col]):
                        new_row[col] = matching_row[col]
                
                improved_matches.append(new_row)
        
        # Convert to DataFrame
        if improved_matches:
            improved_matches_df = pd.DataFrame(improved_matches)
            logger.info(f"Found {len(improved_matches)} improved matches")
            # Add a column to indicate if this is an event match
            if has_event_column:
                improved_matches_df['event_match'] = improved_matches_df['match_reason'] == 'event_match'
            return improved_matches_df
        else:
            logger.info("No improved matches found")
            return pd.DataFrame()
    
    def calculate_total_price(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate the total price based on the factor columns.
        
        Args:
            df: DataFrame with price data
            
        Returns:
            DataFrame with total_price column added
        """
        # Make a copy to avoid modifying the original
        result_df = df.copy()
        
        # Sum the factors directly instead of multiplying
        factor_columns = ['base', 'seasonality', 'dow', 'event']
        for col in factor_columns:
            if col not in result_df.columns:
                logger.warning(f"Column '{col}' not found in DataFrame. Using 0 as default.")
                result_df[col] = 0
        
        # Calculate total price as sum of factors
        result_df['total_price'] = result_df['base'] + result_df['seasonality'] + result_df['dow'] + result_df['event']
        
        return result_df
    
    def generate_summary_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics for the price data.
        
        Args:
            df: DataFrame containing the price data
            
        Returns:
            Dictionary containing summary statistics
        """
        if df.empty:
            logger.warning("Empty DataFrame provided for summary statistics generation.")
            return {}
        
        # Basic statistics
        stats = {
            'total_rows': len(df),
            'date_range': {
                'start': df['date'].min().strftime('%Y-%m-%d'),
                'end': df['date'].max().strftime('%Y-%m-%d')
            }
        }
        
        # Property statistics
        stats['properties'] = df['multiunit_id'].unique().tolist()
        stats['property_count'] = len(stats['properties'])
        
        # Price statistics
        if 'price' in df.columns:
            stats['price'] = {
                'min': df['price'].min(),
                'max': df['price'].max(),
                'mean': df['price'].mean(),
                'median': df['price'].median()
            }
        
        # Factor statistics
        for factor in ['base_price', 'seasonality_factor', 'dow_factor', 'event_factor']:
            if factor in df.columns:
                stats[factor] = {
                    'min': df[factor].min(),
                    'max': df[factor].max(),
                    'mean': df[factor].mean(),
                    'median': df[factor].median()
                }
        
        # Extrapolation statistics
        if 'is_extrapolated' in df.columns:
            extrapolated_count = df['is_extrapolated'].sum()
            stats['extrapolation'] = {
                'extrapolated_count': extrapolated_count,
                'extrapolated_percentage': (extrapolated_count / len(df)) * 100
            }
        
        # Match reason statistics
        if 'match_reason' in df.columns:
            match_reasons = df['match_reason'].value_counts().to_dict()
            stats['match_reasons'] = match_reasons
        
        return stats

    def analyze_event_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze patterns in event data.
        
        Args:
            df: DataFrame containing the price data with event information
            
        Returns:
            Dictionary containing event analysis results
        """
        if df.empty:
            logger.warning("Empty DataFrame provided for event pattern analysis.")
            return {}
        
        # Check if event column exists
        if 'event' not in df.columns:
            logger.warning("No 'event' column found in the data for event pattern analysis.")
            return {'error': "No event data available"}
        
        # Initialize results dictionary
        results = {}
        
        # 1. Event frequency distribution
        event_counts = df['event'].value_counts().to_dict()
        results['event_counts'] = event_counts
        
        # 2. Events by day of week
        df['day_of_week'] = df['date'].dt.day_name()
        events_by_day = df.groupby('day_of_week')['event'].mean().to_dict()
        results['events_by_day'] = events_by_day
        
        # 3. Events by month
        df['month'] = df['date'].dt.month_name()
        events_by_month = df.groupby('month')['event'].mean().to_dict()
        results['events_by_month'] = events_by_month
        
        # 4. Price by event value (if price column exists)
        if 'price' in df.columns:
            # Group by event value and calculate average price
            price_by_event = df.groupby('event')['price'].mean().to_dict()
            results['price_by_event'] = price_by_event
        
        # 5. Event impact on price (if event_factor exists)
        if 'event_factor' in df.columns:
            # Calculate correlation between event value and event factor
            correlation = df['event'].corr(df['event_factor'])
            results['event_factor_correlation'] = correlation
            
            # Group by event value and calculate average event factor
            factor_by_event = df.groupby('event')['event_factor'].mean().to_dict()
            results['factor_by_event'] = factor_by_event
        
        return results
