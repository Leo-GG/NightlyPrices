"""
Standalone web UI for the Nightly Price Analysis.
"""
import os
import sys
import io
import logging
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from contextlib import redirect_stdout

# Add the project root to the path so we can import the nightly_price package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import functions from nightly_price package
from nightly_price.analysis.price_processor import PriceProcessor
from nightly_price.database.connector import DatabaseConnector, test_db_connection
from nightly_price.database.data import PriceDataManager
from nightly_price.visualization.plotter import PricePlotter

# Create function aliases to match the expected interface
def fetch_nightly_prices(db_connector=None, force_fallback=False):
    """Fetch nightly prices from database or generate sample data."""
    data_manager = PriceDataManager()
    return data_manager.fetch_nightly_prices()

def read_cached_data(file_path=None):
    """Read cached data from a file."""
    data_manager = PriceDataManager()
    return data_manager.read_cached_data()

def extrapolate_prices_backward(df):
    """Extrapolate prices backward to January 1, 2024."""
    processor = PriceProcessor()
    return processor.extrapolate_prices_backward(df)

def find_improved_matches(df):
    """Find improved matches for future dates."""
    processor = PriceProcessor()
    return processor.find_improved_matches(df)

def generate_summary_statistics(df):
    """Generate summary statistics for the data."""
    processor = PriceProcessor()
    return processor.generate_summary_statistics(df)

def analyze_event_patterns(df):
    """Analyze event patterns in the data."""
    processor = PriceProcessor()
    return processor.analyze_event_patterns(df)

def plot_price_trends(df):
    """Plot price trends."""
    plotter = PricePlotter()
    return plotter.plot_price_trends(df)

# Note: test_db_connection is now imported directly from the connector module

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NightlyPriceUI:
    """Class for the Nightly Price Analysis Web UI."""
    
    def __init__(self):
        """Initialize the UI."""
        self.setup_page_config()
        self.initialize_session_state()
        
    def setup_page_config(self):
        """Set up the page configuration."""
        st.set_page_config(
            page_title="Nightly Price Analysis",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Custom CSS
        st.markdown("""
        <style>
            .main-header {
                font-size: 2.5rem;
                font-weight: 700;
                color: #1E88E5;
                margin-bottom: 1rem;
            }
            .section-header {
                font-size: 1.8rem;
                font-weight: 600;
                color: #0D47A1;
                margin-top: 2rem;
                margin-bottom: 1rem;
            }
            .subsection-header {
                font-size: 1.4rem;
                font-weight: 500;
                color: #1565C0;
                margin-top: 1.5rem;
                margin-bottom: 0.8rem;
            }
            .info-text {
                font-size: 1rem;
                color: #424242;
            }
            .highlight {
                background-color: #E3F2FD;
                padding: 1rem;
                border-radius: 0.5rem;
                border-left: 0.5rem solid #1E88E5;
            }
            .log-output {
                background-color: #F5F5F5;
                padding: 1rem;
                border-radius: 0.5rem;
                font-family: monospace;
                white-space: pre-wrap;
                overflow-x: auto;
                max-height: 300px;
                overflow-y: auto;
            }
        </style>
        """, unsafe_allow_html=True)
        
    def initialize_session_state(self):
        """Initialize session state variables."""
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        if 'original_data' not in st.session_state:
            st.session_state.original_data = None
        if 'extrapolated_data' not in st.session_state:
            st.session_state.extrapolated_data = None
        if 'improved_matches' not in st.session_state:
            st.session_state.improved_matches = None
        if 'summary_stats' not in st.session_state:
            st.session_state.summary_stats = None
        if 'event_analysis' not in st.session_state:
            st.session_state.event_analysis = None
        if 'log_output' not in st.session_state:
            st.session_state.log_output = {}
            
    def run(self):
        """Run the UI."""
        # Header
        st.markdown('<div class="main-header">Nightly Price Analysis Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div class="info-text">Analyze nightly rental price data, extrapolate prices backward, and find improved matches for future dates.</div>', unsafe_allow_html=True)
        
        # Main method to run the UI
        self.render_sidebar()
        self.render_main_content()
        
    def render_sidebar(self):
        """Render the sidebar."""
        st.sidebar.markdown('<div class="subsection-header">Data Source</div>', unsafe_allow_html=True)
        
        # Data source selection
        data_source = st.sidebar.radio(
            "Select data source:",
            ["Load from cached file", "Fetch from database", "Upload CSV file"]
        )
        
        # Load data button
        load_data_button = st.sidebar.button("Load Data", key="load_data_button")
        
        # File uploader (only shown when upload option is selected)
        uploaded_file = None
        if data_source == "Upload CSV file":
            uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
        
        # Always show process steps, but disable buttons if data not loaded
        st.sidebar.markdown('<div class="subsection-header">Processing Steps</div>', unsafe_allow_html=True)
        
        # Run all steps button
        run_all_steps = st.sidebar.button(
            "Run All Analysis Steps", 
            key="run_all_steps_button",
            help="Run all analysis steps in sequence"
        )
        
        # Individual steps
        extrapolate_button = st.sidebar.button(
            "1. Extrapolate Prices Backward", 
            key="extrapolate_btn"
        )
        
        find_matches_button = st.sidebar.button(
            "2. Find Improved Matches", 
            key="find_matches_btn"
        )
        
        summary_stats_button = st.sidebar.button(
            "3. Generate Summary Statistics", 
            key="summary_stats_btn"
        )
        
        event_analysis_button = st.sidebar.button(
            "4. Analyze Event Patterns", 
            key="event_analysis_btn"
        )
        
        # Export data
        st.sidebar.markdown('<div class="subsection-header">Export Data</div>', unsafe_allow_html=True)
        
        export_button = st.sidebar.button(
            "Export to CSV", 
            key="export_button"
        )
        
        # Handle data loading
        if load_data_button or (uploaded_file is not None and data_source == "Upload CSV file"):
            with st.spinner("Loading data..."):
                try:
                    if data_source == "Load from cached file":
                        result, output = self._capture_output(read_cached_data)
                        st.session_state.original_data = result
                        st.session_state.log_output['data_loading'] = output
                        
                    elif data_source == "Fetch from database":
                        # Test database connection first
                        connection_result = test_db_connection()
                        if connection_result['success']:
                            # Connection successful, fetch data
                            result, output = self._capture_output(fetch_nightly_prices)
                            st.session_state.original_data = result
                            st.session_state.log_output['data_loading'] = output
                        else:
                            # Connection failed, show error and use fallback
                            st.sidebar.error(f"Database connection failed: {connection_result['error']}")
                            st.sidebar.info("Using fallback data instead.")
                            result, output = self._capture_output(read_cached_data)
                            st.session_state.original_data = result
                            st.session_state.log_output['data_loading'] = f"Database error: {connection_result['error']}\n{output}"
                            
                    elif data_source == "Upload CSV file" and uploaded_file is not None:
                        # Read uploaded file
                        df = pd.read_csv(uploaded_file)
                        # Convert date column to datetime
                        df['date'] = pd.to_datetime(df['date'])
                        st.session_state.original_data = df
                        st.session_state.log_output['data_loading'] = f"Loaded data from uploaded file: {uploaded_file.name}"
                    
                    # Set data loaded flag
                    if st.session_state.original_data is not None:
                        st.session_state.data_loaded = True
                        st.sidebar.success("Data loaded successfully!")
                    else:
                        st.sidebar.error("Failed to load data.")
                        
                except Exception as e:
                    st.sidebar.error(f"Error loading data: {str(e)}")
                    logging.error(f"Error loading data: {e}", exc_info=True)
        
        # Handle run all steps button
        if run_all_steps:
            self._run_all_analysis_steps()
        
        # Handle individual step buttons
        if extrapolate_button:
            self._run_extrapolation()
            
        if find_matches_button:
            self._run_find_matches()
            
        if summary_stats_button:
            self._run_summary_statistics()
            
        if event_analysis_button:
            self._run_event_analysis()
            
        # Handle export button
        if export_button:
            self._export_data()
            
    def render_main_content(self):
        """Render the main content."""
        # Create tabs for different analysis results
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Original Data", 
            "Extrapolated Data", 
            "Improved Matches", 
            "Summary Statistics", 
            "Event Analysis",
            "Visualizations"
        ])
        
        # Tab 1: Original Data
        with tab1:
            st.markdown('<div class="section-header">Original Data</div>', unsafe_allow_html=True)
            
            if 'data_loading' in st.session_state.log_output:
                st.markdown('<div class="subsection-header">Log Output</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="log-output">{st.session_state.log_output["data_loading"]}</div>', unsafe_allow_html=True)
            
            if st.session_state.original_data is not None:
                st.markdown('<div class="subsection-header">Data Preview</div>', unsafe_allow_html=True)
                st.dataframe(st.session_state.original_data, use_container_width=True)
                
                st.markdown('<div class="subsection-header">Data Summary</div>', unsafe_allow_html=True)
                st.markdown(f"**Total rows:** {len(st.session_state.original_data)}")
                # Convert numpy.int64 values to strings before joining
                property_ids = [str(prop_id) for prop_id in st.session_state.original_data['multiunit_id'].unique()]
                st.markdown(f"**Properties:** {', '.join(property_ids)}")
                st.markdown(f"**Date range:** {st.session_state.original_data['date'].min().strftime('%Y-%m-%d')} to {st.session_state.original_data['date'].max().strftime('%Y-%m-%d')}")
                
                # Show data distribution
                st.markdown('<div class="subsection-header">Data Distribution</div>', unsafe_allow_html=True)
                
                # Count by property
                property_counts = st.session_state.original_data['multiunit_id'].value_counts().reset_index()
                property_counts.columns = ['Property', 'Count']
                # Convert property IDs to strings to treat them as names, not numbers
                property_counts['Property'] = property_counts['Property'].astype(str)
                
                # Create bar chart with vertical x-axis labels
                fig = px.bar(property_counts, x='Property', y='Count',
                            title='Number of Records by Property',
                            labels={'Count': 'Number of Records', 'Property': 'Property ID'})
                
                # Update layout to make x-axis labels vertical
                fig.update_layout(
                    xaxis=dict(
                        tickmode='array',
                        tickvals=list(range(len(property_counts))),
                        ticktext=property_counts['Property'],
                        tickangle=90,  # Vertical labels
                        type='category'  # Treat as categorical
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Tab 2: Extrapolated Data
        with tab2:
            st.markdown('<div class="section-header">Extrapolated Data</div>', unsafe_allow_html=True)
            
            if 'extrapolation' in st.session_state.log_output:
                st.markdown('<div class="subsection-header">Log Output</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="log-output">{st.session_state.log_output["extrapolation"]}</div>', unsafe_allow_html=True)
            
            if st.session_state.extrapolated_data is not None:
                st.markdown('<div class="subsection-header">Data Preview</div>', unsafe_allow_html=True)
                
                # Function to determine if a date is extrapolated
                def is_extrapolated(date_str):
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    return "Extrapolated" if date < datetime(2024, 9, 1) else "Original"
                
                # Create a temporary dataframe with the source column
                temp_df = st.session_state.extrapolated_data.copy()
                temp_df['source'] = temp_df['date'].dt.strftime('%Y-%m-%d').apply(is_extrapolated)
                
                st.dataframe(temp_df, use_container_width=True)
                
                # Show extrapolation summary
                st.markdown('<div class="subsection-header">Extrapolation Summary</div>', unsafe_allow_html=True)
                
                # Count by source
                source_counts = temp_df['source'].value_counts().reset_index()
                source_counts.columns = ['Source', 'Count']
                
                fig = px.pie(source_counts, values='Count', names='Source',
                            title='Distribution of Original vs. Extrapolated Data',
                            color_discrete_map={'Original': '#1E88E5', 'Extrapolated': '#FFC107'})
                st.plotly_chart(fig, use_container_width=True)
        
        # Tab 3: Improved Matches
        with tab3:
            st.markdown('<div class="section-header">Improved Matches</div>', unsafe_allow_html=True)
            
            if 'improved_matches' in st.session_state.log_output:
                st.markdown('<div class="subsection-header">Log Output</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="log-output">{st.session_state.log_output["improved_matches"]}</div>', unsafe_allow_html=True)
            
            if st.session_state.improved_matches is not None:
                # Check if the improved_matches DataFrame has the expected columns
                if 'improved_match' in st.session_state.improved_matches.columns:
                    improved_count = (st.session_state.improved_matches['improved_match'] == True).sum()
                    total_count = len(st.session_state.improved_matches)
                    improvement_rate = improved_count / total_count * 100 if total_count > 0 else 0
                    
                    st.markdown(f"**Improved matches:** {improved_count} out of {total_count} ({improvement_rate:.2f}%)")
                else:
                    # Display available columns and a message about the missing column
                    st.warning("The 'improved_match' column was not found in the improved matches data.")
                    st.markdown("**Available columns:**")
                    st.write(", ".join(st.session_state.improved_matches.columns.tolist()))
                    
                    # Try to identify a similar column that might contain the improved match information
                    possible_columns = [col for col in st.session_state.improved_matches.columns if 'match' in col.lower() or 'improv' in col.lower()]
                    if possible_columns:
                        st.markdown("**Possible alternative columns:**")
                        st.write(", ".join(possible_columns))
                
                # Display the dataframe regardless of column presence
                st.dataframe(st.session_state.improved_matches)
            else:
                st.info("Run the 'Find Improved Matches' step to see results here.")
        
        # Tab 4: Summary Statistics
        with tab4:
            st.markdown('<div class="section-header">Summary Statistics</div>', unsafe_allow_html=True)
            
            if 'summary_stats' in st.session_state.log_output:
                st.markdown('<div class="subsection-header">Log Output</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="log-output">{st.session_state.log_output["summary_stats"]}</div>', unsafe_allow_html=True)
            
            if st.session_state.summary_stats is not None:
                st.markdown('<div class="subsection-header">Data Preview</div>', unsafe_allow_html=True)
                
                # Convert the nested dictionary to a more user-friendly format for display
                if isinstance(st.session_state.summary_stats, dict):
                    # Create a flattened version for display
                    flat_stats = {}
                    for key, value in st.session_state.summary_stats.items():
                        if isinstance(value, dict):
                            for subkey, subvalue in value.items():
                                flat_stats[f"{key}_{subkey}"] = subvalue
                        else:
                            flat_stats[key] = value
                    
                    # Display the flattened stats
                    st.dataframe(pd.DataFrame([flat_stats]), use_container_width=True)
                else:
                    st.dataframe(st.session_state.summary_stats, use_container_width=True)
                
                # Show summary visualizations
                st.markdown('<div class="subsection-header">Price Statistics by Property</div>', unsafe_allow_html=True)
                
                # Create a DataFrame for visualization
                if 'properties' in st.session_state.summary_stats and 'price' in st.session_state.summary_stats:
                    # Extract properties and price statistics
                    properties = st.session_state.summary_stats['properties']
                    
                    # Create a DataFrame with price statistics for each property
                    price_stats_data = []
                    for prop in properties:
                        # Filter the original data for this property
                        if st.session_state.extrapolated_data is not None:
                            prop_data = st.session_state.extrapolated_data[
                                st.session_state.extrapolated_data['multiunit_id'] == prop
                            ]
                            
                            if not prop_data.empty and 'price' in prop_data.columns:
                                price_stats_data.append({
                                    'multiunit_id': str(prop),
                                    'min_price': prop_data['price'].min(),
                                    'avg_price': prop_data['price'].mean(),
                                    'max_price': prop_data['price'].max()
                                })
                    
                    if price_stats_data:
                        price_stats_df = pd.DataFrame(price_stats_data)
                        price_stats_df['multiunit_id'] = price_stats_df['multiunit_id'].astype(str)

                        # Bar chart of min, max, avg prices by property
                        fig = px.bar(price_stats_df, x='multiunit_id', y=['min_price', 'avg_price', 'max_price'],
                                    title='Price Statistics by Property',
                                    labels={'multiunit_id': 'Property', 'value': 'Price ($)', 'variable': 'Statistic'},
                                    barmode='group')

                        # Update layout to make x-axis labels vertical
                        fig.update_layout(
                            xaxis=dict(
                                tickmode='array',
                                tickvals=list(range(len(property_counts))),
                                ticktext=property_counts['Property'],
                        tickangle=90,  # Vertical labels
                        type='category'  # Treat as categorical
                    )
                )
                        st.plotly_chart(fig, use_container_width=True)

                        
                    else:
                        st.info("No price data available for visualization.")
                else:
                    st.info("No property or price data available for visualization.")
        
        # Tab 5: Event Analysis
        with tab5:
            st.markdown('<div class="section-header">Event Analysis Results</div>', unsafe_allow_html=True)
            
            if 'event_analysis' in st.session_state.log_output:
                st.markdown('<div class="subsection-header">Log Output</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="log-output">{st.session_state.log_output["event_analysis"]}</div>', unsafe_allow_html=True)
            
            if st.session_state.event_analysis is not None:
                # Handle the event analysis results
                if isinstance(st.session_state.event_analysis, dict):
                    # Display event counts
                    if 'event_counts' in st.session_state.event_analysis:
                        st.markdown('<div class="subsection-header">Event Frequency</div>', unsafe_allow_html=True)
                        event_counts = st.session_state.event_analysis['event_counts']
                        if event_counts:
                            # Convert to DataFrame for visualization
                            event_counts_df = pd.DataFrame(
                                {'event_value': list(event_counts.keys()), 'count': list(event_counts.values())}
                            )
                            st.dataframe(event_counts_df, use_container_width=True)
                            
                            # Create bar chart
                            fig = px.bar(event_counts_df[event_counts_df['event_value'] > 0], x='event_value', y='count',
                                        title='Event Frequency Distribution',
                                        labels={'event_value': 'Event Value', 'count': 'Frequency'})
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Display events by day of week
                    if 'events_by_day' in st.session_state.event_analysis:
                        st.markdown('<div class="subsection-header">Events by Day of Week</div>', unsafe_allow_html=True)
                        events_by_day = st.session_state.event_analysis['events_by_day']
                        if events_by_day:
                            # Convert to DataFrame for visualization
                            events_by_day_df = pd.DataFrame(
                                {'day_of_week': list(events_by_day.keys()), 'avg_event_value': list(events_by_day.values())}
                            )
                            st.dataframe(events_by_day_df, use_container_width=True)
                            
                            # Create bar chart
                            fig = px.bar(events_by_day_df, x='day_of_week', y='avg_event_value',
                                        title='Average Event Value by Day of Week',
                                        labels={'day_of_week': 'Day of Week', 'avg_event_value': 'Average Event Value'})
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Display events by month
                    if 'events_by_month' in st.session_state.event_analysis:
                        st.markdown('<div class="subsection-header">Events by Month</div>', unsafe_allow_html=True)
                        events_by_month = st.session_state.event_analysis['events_by_month']
                        if events_by_month:
                            # Convert to DataFrame for visualization
                            events_by_month_df = pd.DataFrame(
                                {'month': list(events_by_month.keys()), 'avg_event_value': list(events_by_month.values())}
                            )
                            st.dataframe(events_by_month_df, use_container_width=True)
                            
                            # Create bar chart
                            fig = px.bar(events_by_month_df, x='month', y='avg_event_value',
                                        title='Average Event Value by Month',
                                        labels={'month': 'Month', 'avg_event_value': 'Average Event Value'})
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Display price by event value
                    if 'price_by_event' in st.session_state.event_analysis:
                        st.markdown('<div class="subsection-header">Price by Event Value</div>', unsafe_allow_html=True)
                        price_by_event = st.session_state.event_analysis['price_by_event']
                        if price_by_event:
                            # Convert to DataFrame for visualization
                            price_by_event_df = pd.DataFrame(
                                {'event_value': list(price_by_event.keys()), 'avg_price': list(price_by_event.values())}
                            )
                            st.dataframe(price_by_event_df, use_container_width=True)
                            
                            # Create bar chart
                            fig = px.bar(price_by_event_df, x='event_value', y='avg_price',
                                        title='Average Price by Event Value',
                                        labels={'event_value': 'Event Value', 'avg_price': 'Average Price'})
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    # If it's not a dictionary, just display it as is
                    st.dataframe(st.session_state.event_analysis, use_container_width=True)
        
        # Tab 6: Visualizations
        with tab6:
            st.markdown('<div class="section-header">Visualizations</div>', unsafe_allow_html=True)
            
            if st.session_state.extrapolated_data is not None:
                # Select property for visualization
                properties = st.session_state.extrapolated_data['multiunit_id'].unique()
                # Convert numpy values to native Python types for the selectbox
                properties_list = [str(prop) for prop in properties]
                
                if properties_list:
                    selected_property = st.selectbox("Select Property for Visualization", properties_list, key="viz_property_select")
                    
                    # Convert selected_property to the appropriate type if needed
                    try:
                        # Try to convert to int if the original was numeric
                        if st.session_state.extrapolated_data['multiunit_id'].dtype.kind in 'iu':  # integer types
                            selected_property = int(selected_property)
                    except (ValueError, TypeError):
                        # If conversion fails, keep as string
                        pass
                    
                    # Filter data for selected property
                    property_data = st.session_state.extrapolated_data[
                        st.session_state.extrapolated_data['multiunit_id'] == selected_property
                    ].copy()
                    
                    if not property_data.empty and 'date' in property_data.columns:
                        # Ensure date is datetime
                        if property_data['date'].dtype != 'datetime64[ns]':
                            property_data['date'] = pd.to_datetime(property_data['date'])
                        
                        # Sort by date for proper trend visualization
                        property_data = property_data.sort_values('date')
                        
                        # Check which factors are available
                        available_factors = []
                        for factor in ['dow', 'event', 'seasonality']:
                            if factor in property_data.columns:
                                available_factors.append(factor)
                        
                        if not available_factors:
                            st.warning("No factor columns (dow, event, seasonality) found in the data.")
                        else:
                            # Day of Week (DOW) Factor Trend
                            if 'dow' in available_factors:
                                st.markdown('<div class="subsection-header">Day of Week (DOW) Factor Trend</div>', unsafe_allow_html=True)
                                
                                # Create figure for DOW factor
                                fig = px.line(property_data, x='date', y='dow',
                                            title=f'DOW Factor Trend for Property {selected_property}',
                                            labels={'date': 'Date', 'dow': 'DOW Factor'})
                                
                                # Add markers for extrapolated data points if the column exists
                                if 'is_extrapolated' in property_data.columns:
                                    extrapolated_data = property_data[property_data['is_extrapolated'] == True]
                                    if not extrapolated_data.empty and 'dow' in extrapolated_data.columns:
                                        fig.add_scatter(x=extrapolated_data['date'], y=extrapolated_data['dow'],
                                                        mode='markers', name='Extrapolated', marker=dict(color='red', size=8))
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # DOW Factor Distribution
                                fig = px.histogram(property_data, x='dow', nbins=20,
                                                title=f'DOW Factor Distribution for Property {selected_property}',
                                                labels={'dow': 'DOW Factor', 'count': 'Frequency'})
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Event Factor Trend
                            if 'event' in available_factors:
                                st.markdown('<div class="subsection-header">Event Factor Trend</div>', unsafe_allow_html=True)
                                
                                # Create figure for Event factor
                                fig = px.line(property_data, x='date', y='event',
                                            title=f'Event Factor Trend for Property {selected_property}',
                                            labels={'date': 'Date', 'event': 'Event Factor'})
                                
                                # Add markers for extrapolated data points if the column exists
                                if 'is_extrapolated' in property_data.columns:
                                    extrapolated_data = property_data[property_data['is_extrapolated'] == True]
                                    if not extrapolated_data.empty and 'event' in extrapolated_data.columns:
                                        fig.add_scatter(x=extrapolated_data['date'], y=extrapolated_data['event'],
                                                        mode='markers', name='Extrapolated', marker=dict(color='red', size=8))
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Event Factor Distribution
                                fig = px.histogram(property_data, x='event', nbins=20,
                                                title=f'Event Factor Distribution for Property {selected_property}',
                                                labels={'event': 'Event Factor', 'count': 'Frequency'})
                                st.plotly_chart(fig, use_container_width=True)
                            
                            # Seasonality Factor Trend
                            if 'seasonality' in available_factors:
                                st.markdown('<div class="subsection-header">Seasonality Factor Trend</div>', unsafe_allow_html=True)
                                
                                # Create figure for Seasonality factor
                                fig = px.line(property_data, x='date', y='seasonality',
                                            title=f'Seasonality Factor Trend for Property {selected_property}',
                                            labels={'date': 'Date', 'seasonality': 'Seasonality Factor'})
                                
                                # Add markers for extrapolated data points if the column exists
                                if 'is_extrapolated' in property_data.columns:
                                    extrapolated_data = property_data[property_data['is_extrapolated'] == True]
                                    if not extrapolated_data.empty and 'seasonality' in extrapolated_data.columns:
                                        fig.add_scatter(x=extrapolated_data['date'], y=extrapolated_data['seasonality'],
                                                        mode='markers', name='Extrapolated', marker=dict(color='red', size=8))
                                
                                st.plotly_chart(fig, use_container_width=True)
                                
                                # Seasonality Factor Distribution
                                fig = px.histogram(property_data, x='seasonality', nbins=20,
                                                title=f'Seasonality Factor Distribution for Property {selected_property}',
                                                labels={'seasonality': 'Seasonality Factor', 'count': 'Frequency'})
                                st.plotly_chart(fig, use_container_width=True)
                        
                        # Monthly average factors
                        st.markdown('<div class="subsection-header">Monthly Average Factors</div>', unsafe_allow_html=True)
                        
                        # Add year-month column for grouping
                        property_data['year_month'] = property_data['date'].dt.strftime('%Y-%m')
                        
                        # Check which factors are available
                        available_factors = []
                        for factor in ['dow', 'event', 'seasonality']:
                            if factor in property_data.columns:
                                available_factors.append(factor)
                        
                        if not available_factors:
                            st.warning("No factor columns (dow, event, seasonality) found in the data.")
                        else:
                            # Create a figure for monthly averages of each factor
                            for factor in available_factors:
                                # Group by year-month and calculate average factor
                                monthly_avg = property_data.groupby('year_month')[factor].mean().reset_index()
                                
                                # Sort by year-month
                                monthly_avg = monthly_avg.sort_values('year_month')
                                
                                # Create bar chart
                                fig = px.bar(monthly_avg, x='year_month', y=factor,
                                            title=f'Monthly Average {factor.capitalize()} Factor for Property {selected_property}',
                                            labels={'year_month': 'Month', factor: f'Average {factor.capitalize()} Factor'})
                                
                                # Update x-axis to show labels vertically
                                fig.update_layout(
                                    xaxis=dict(
                                        tickangle=90,  # Vertical labels
                                        type='category'  # Treat as categorical
                                    )
                                )
                                
                                st.plotly_chart(fig, use_container_width=True)
                        
                        # Factor components comparison
                        factor_columns = [col for col in property_data.columns if col in ['base', 'seasonality', 'dow', 'event']]
                        if len(factor_columns) >= 2:  # Need at least 2 factors to compare
                            st.markdown('<div class="subsection-header">Factor Components Comparison</div>', unsafe_allow_html=True)
                            
                            # Create a DataFrame for the components
                            components_data = pd.DataFrame({
                                'date': property_data['date']
                            })
                            
                            # Add available factors with proper capitalized names
                            factor_display_names = {
                                'base': 'Base',
                                'seasonality': 'Seasonality',
                                'dow': 'Day of Week',
                                'event': 'Event'
                            }
                            
                            for factor in factor_columns:
                                components_data[factor_display_names[factor]] = property_data[factor]
                            
                            # Melt the DataFrame for Plotly
                            value_vars = [factor_display_names[factor] for factor in factor_columns]
                            melted_data = pd.melt(components_data, id_vars=['date'], 
                                                value_vars=value_vars,
                                                var_name='Factor', value_name='Value')
                            
                            # Create line chart comparing all factors
                            fig = px.line(melted_data, x='date', y='Value', color='Factor',
                                        title=f'Factor Components Comparison for Property {selected_property}',
                                        labels={'date': 'Date', 'Value': 'Factor Value', 'Factor': 'Factor Type'})
                            
                            # Add markers for extrapolated data points if the column exists
                            if 'is_extrapolated' in property_data.columns:
                                extrapolated_dates = property_data[property_data['is_extrapolated'] == True]['date'].unique()
                                if len(extrapolated_dates) > 0:
                                    # Add a vertical line at the boundary between original and extrapolated data
                                    boundary_date = extrapolated_dates.max()
                                    fig.add_vline(x=boundary_date, line_width=2, line_dash="dash", line_color="red")
                                    fig.add_annotation(
                                        x=boundary_date,
                                        y=melted_data['Value'].max() * 0.9,
                                        text="Extrapolation Boundary",
                                        showarrow=True,
                                        arrowhead=1
                                    )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Match reasons distribution
                        if 'match_reason' in property_data.columns:
                            st.markdown('<div class="subsection-header">Match Reasons Distribution</div>', unsafe_allow_html=True)
                            
                            # Count match reasons
                            match_counts = property_data['match_reason'].value_counts().reset_index()
                            match_counts.columns = ['Match Reason', 'Count']
                            
                            fig = px.pie(match_counts, values='Count', names='Match Reason',
                                        title=f'Match Reasons Distribution for Property {selected_property}')
                            
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("No price or date data available for the selected property.")
                else:
                    st.warning("No properties available for visualization.")
            else:
                st.warning("No data available for visualization. Please load and process data first.")
    
    def _capture_output(self, func, *args, **kwargs):
        """Capture stdout output from a function call."""
        f = io.StringIO()
        with redirect_stdout(f):
            result = func(*args, **kwargs)
        output = f.getvalue()
        return result, output
    
    def _run_extrapolation(self):
        """Run price extrapolation step."""
        if st.session_state.original_data is not None:
            with st.spinner("Extrapolating prices..."):
                result, output = self._capture_output(
                    extrapolate_prices_backward, 
                    st.session_state.original_data
                )
                st.session_state.extrapolated_data = result
                st.session_state.log_output['extrapolation'] = output
                return True
        return False
    
    def _run_find_matches(self):
        """Run find improved matches step."""
        if st.session_state.extrapolated_data is not None:
            with st.spinner("Finding improved matches..."):
                result, output = self._capture_output(
                    find_improved_matches, 
                    st.session_state.extrapolated_data
                )
                st.session_state.improved_matches = result
                st.session_state.log_output['improved_matches'] = output
                return True
        return False
    
    def _run_summary_statistics(self):
        """Run summary statistics step."""
        if st.session_state.extrapolated_data is not None:
            with st.spinner("Generating summary statistics..."):
                result, output = self._capture_output(
                    generate_summary_statistics, 
                    st.session_state.extrapolated_data
                )
                st.session_state.summary_stats = result
                st.session_state.log_output['summary_stats'] = output
                return True
        return False
    
    def _run_event_analysis(self):
        """Run event analysis step."""
        if st.session_state.extrapolated_data is not None:
            with st.spinner("Analyzing event patterns..."):
                result, output = self._capture_output(
                    analyze_event_patterns, 
                    st.session_state.extrapolated_data
                )
                st.session_state.event_analysis = result
                st.session_state.log_output['event_analysis'] = output
                return True
        return False
    
    def _run_all_analysis_steps(self):
        """Run all analysis steps in sequence."""
        if st.session_state.data_loaded and st.session_state.original_data is not None:
            with st.spinner("Running all analysis steps..."):
                # Step 1: Extrapolate prices
                self._run_extrapolation()
               
                # Step 3: Find improved matches
                self._run_find_matches()
                
                # Step 4: Generate summary statistics
                self._run_summary_statistics()
                
                # Step 5: Analyze event patterns
                self._run_event_analysis()
                
                return True
        return False
    
    def _export_data(self):
        """Export data to CSV files."""
        try:
            # Create output directory if it doesn't exist
            output_dir = os.path.join(os.getcwd(), 'output')
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Save complete data
            if st.session_state.extrapolated_data is not None:
                st.session_state.extrapolated_data.to_csv(f'{output_dir}/nightly_prices_complete.csv', index=False)
            
            # Save improved matches
            if st.session_state.improved_matches is not None:
                st.session_state.improved_matches.to_csv(f'{output_dir}/improved_matches.csv', index=False)
            
            # Save summary statistics
            if st.session_state.summary_stats is not None:
                # Check if summary_stats is a dictionary
                if isinstance(st.session_state.summary_stats, dict):
                    # Convert the dictionary to a DataFrame
                    summary_df = pd.DataFrame(st.session_state.summary_stats.items(), columns=['Metric', 'Value'])
                    summary_df.to_csv(f'{output_dir}/price_summary.csv', index=False)
                else:
                    # If it's already a DataFrame, save directly
                    st.session_state.summary_stats.to_csv(f'{output_dir}/price_summary.csv', index=False)
            
            # Save event analysis
            if st.session_state.event_analysis is not None:
                for key, value in st.session_state.event_analysis.items():
                    value.to_csv(f'{output_dir}/{key}.csv', index=False)
            
            st.sidebar.success(f"Data exported to {output_dir} directory!")
            
        except Exception as e:
            st.sidebar.error(f"Error exporting data: {str(e)}")
            logging.error(f"Error exporting data: {e}", exc_info=True)

def main():
    """Main function to run the web UI."""
    try:
        # Create UI instance and run
        ui = NightlyPriceUI()
        ui.run()
    except Exception as e:
        logging.error(f"Error running web UI: {e}", exc_info=True)
        st.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
