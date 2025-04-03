"""
Main application module for nightly price analysis.
"""
import os
import logging
import argparse
import pandas as pd
from typing import Dict, Any, Optional, List

from meshu.utils.logger import configure_root_logger
from meshu.database.fallback import RobustDataFetcher
from meshu.analysis.price_processor import PriceProcessor
from meshu.analysis.statistics import PriceAnalyzer
from meshu.visualization.plotter import PricePlotter

# Configure root logger
configure_root_logger(level=logging.INFO)

# Module logger
logger = logging.getLogger(__name__)

# Define multiunit IDs
MULTIUNIT_IDS = [
    '2789103', '3134165', '3134168', '3482048', '3592887', '3603346', '3739908',
    '3824642', '3824643', '3867371', '3867385'
]


class NightlyPriceAnalysis:
    """Main class for nightly price analysis."""
    
    def __init__(
        self,
        output_dir: str = 'output',
        cache_dir: str = 'data',
        use_cached_data: bool = False,
        force_fallback: bool = False
    ):
        """
        Initialize the nightly price analysis.
        
        Args:
            output_dir: Directory to save output files
            cache_dir: Directory to store cached data
            use_cached_data: Whether to use cached data if available
            force_fallback: Whether to force using fallback data
        """
        self.output_dir = output_dir
        self.plots_dir = os.path.join(output_dir, 'plots')
        self.cache_dir = cache_dir
        self.use_cached_data = use_cached_data
        self.force_fallback = force_fallback
        
        # Create output directories
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        if not os.path.exists(self.plots_dir):
            os.makedirs(self.plots_dir)
        
        # Initialize components
        self.data_fetcher = RobustDataFetcher(cache_dir=cache_dir)
        self.price_processor = PriceProcessor()
        self.price_analyzer = PriceAnalyzer()
        self.price_plotter = PricePlotter(output_dir=self.plots_dir)
    
    def run(self, multiunit_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run the nightly price analysis.
        
        Args:
            multiunit_ids: List of multiunit IDs to analyze
            
        Returns:
            Dictionary with analysis results
        """
        logger.info("Starting nightly price analysis...")
        
        if multiunit_ids is None:
            multiunit_ids = MULTIUNIT_IDS
        
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
        
        # Fetch data
        logger.info("Fetching nightly price data...")
        df = self.data_fetcher.fetch_data(
            query=query,
            multiunit_ids=multiunit_ids,
            use_cache=self.use_cached_data,
            force_fallback=self.force_fallback
        )
        
        # Extrapolate prices back to January 1, 2024
        logger.info("Extrapolating prices backward...")
        combined_df = self.price_processor.extrapolate_prices_backward(df)
        
        # Calculate total prices
        logger.info("Calculating total prices...")
        combined_df = self.price_processor.calculate_total_price(combined_df)
        
        # Find improved '-1 year' matches
        logger.info("Finding improved matches...")
        matches_df = self.price_processor.find_improved_matches(combined_df)
        
        # Generate summary statistics
        logger.info("Generating summary statistics...")
        summary_df = self.price_analyzer.generate_summary_statistics(combined_df)
        
        # Analyze event patterns
        logger.info("Analyzing event patterns...")
        event_analysis = self.price_analyzer.analyze_event_patterns(combined_df)
        
        # Detect seasonal patterns
        logger.info("Detecting seasonal patterns...")
        seasonal_patterns = self.price_analyzer.detect_seasonal_patterns(combined_df)
        
        # Create visualizations
        logger.info("Creating visualizations...")
        self.price_plotter.plot_price_trends(combined_df)
        self.price_plotter.plot_seasonal_patterns(combined_df)
        self.price_plotter.plot_weekday_patterns(combined_df)
        self.price_plotter.plot_price_distribution(combined_df)
        
        # Save results to CSV
        logger.info(f"Saving results to CSV files in '{self.output_dir}' directory...")
        combined_df.to_csv(f'{self.output_dir}/nightly_prices_complete.csv', index=False)
        matches_df.to_csv(f'{self.output_dir}/improved_matches.csv', index=False)
        summary_df.to_csv(f'{self.output_dir}/price_summary.csv', index=False)
        seasonal_patterns.to_csv(f'{self.output_dir}/seasonal_patterns.csv', index=False)
        
        for key, value in event_analysis.items():
            value.to_csv(f'{self.output_dir}/{key}.csv', index=False)
        
        # Save results to Excel with multiple sheets
        logger.info("Creating Excel file with multiple sheets...")
        with pd.ExcelWriter(f'{self.output_dir}/nightly_price_analysis.xlsx') as writer:
            combined_df.to_excel(writer, sheet_name='Complete Price Data', index=False)
            matches_df.to_excel(writer, sheet_name='Improved Matches', index=False)
            summary_df.to_excel(writer, sheet_name='Summary Statistics', index=False)
            seasonal_patterns.to_excel(writer, sheet_name='Seasonal Patterns', index=False)
            
            for key, value in event_analysis.items():
                value.to_excel(writer, sheet_name=key[:31], index=False)  # Excel sheet names limited to 31 chars
        
        logger.info(f"Analysis complete. Results saved to '{self.output_dir}' directory.")
        
        # Print sample of the results
        logger.info("\nSample of the complete price data:")
        print(combined_df.head())
        
        logger.info("\nSample of the improved matches:")
        print(matches_df.head())
        
        return {
            "complete_data": combined_df,
            "improved_matches": matches_df,
            "summary_statistics": summary_df,
            "seasonal_patterns": seasonal_patterns,
            "event_analysis": event_analysis
        }


def main():
    """Main function to run the analysis from command line."""
    parser = argparse.ArgumentParser(description='Nightly Price Analysis')
    parser.add_argument('--fetch', action='store_true', help='Force fetch data from database')
    parser.add_argument('--no-cache', action='store_true', help='Do not use cached data')
    parser.add_argument('--fallback', action='store_true', help='Force using fallback data')
    parser.add_argument('--output-dir', type=str, default='output', help='Output directory')
    parser.add_argument('--cache-dir', type=str, default='data', help='Cache directory')
    args = parser.parse_args()
    
    # Initialize and run analysis
    analysis = NightlyPriceAnalysis(
        output_dir=args.output_dir,
        cache_dir=args.cache_dir,
        use_cached_data=not args.no_cache,
        force_fallback=args.fallback
    )
    
    analysis.run()


if __name__ == "__main__":
    main()
