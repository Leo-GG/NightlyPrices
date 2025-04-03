# Nightly Price Analysis

This project implements the requirements for analyzing and extrapolating nightly rental price data for multiple properties.

## Overview

The implementation handles two main tasks:

1. **Extrapolating Prices Backward**: Fills in daily prices from January 1, 2024, through September 2, 2024, using data from the corresponding dates in 2025.

2. **Finding Improved "-1 Year" Matches**: Implements a more intelligent approach to matching future dates with corresponding dates from the previous year, respecting weekday and event alignments.

## Implementation Details

### Data Generation

Since the actual data isn't available, the code generates sample data that follows the structure described in the requirements:
- Base price for each property
- Seasonality factors (higher in summer and holidays)
- Day-of-week factors (higher on weekends)
- Event factors for special dates

### Price Extrapolation Approach

For extrapolating prices back to January 1, 2024:

1. **Base Price**: Uses the same base price as in the existing data for each property.
2. **Seasonality**: Uses the seasonality factor from the corresponding "+1 year" date.
3. **Day-of-Week (DOW)**: Averages DOW values from dates with the same weekday in the existing data.
4. **Event**: Assumes events recur on the same calendar dates one year apart.

### Improved "-1 Year" Matches Approach

For finding better matches between future dates and past dates:

1. **Event Alignment**: When a future date has an event factor > 1.0, the algorithm prioritizes finding a past date with a similar event factor, even if the weekday differs.
2. **Weekday Alignment**: When a future date has no special event, the algorithm finds the nearest date with the same weekday.
3. **Handling Special Cases**: 
   - For events that don't exist in both years, the algorithm falls back to the closest date with similar characteristics.
   - For partial overlaps, it prioritizes event matching over weekday matching.

## Output Files

The program generates several output files:

1. **nightly_prices_complete.csv**: Complete dataset with original and extrapolated data.
2. **improved_matches.csv**: Details of the improved "-1 year" matches.
3. **price_summary.csv**: Summary statistics for each property.
4. **nightly_price_analysis.xlsx**: Excel file with all data in separate sheets.
5. **Visualization plots**: Price trends and factor visualizations for selected properties.

## How to Run

### Command Line Interface

```bash
python app.py analysis
```

The script will:
1. Fetch or load cached data
2. Perform the extrapolation and matching
3. Create visualizations
4. Save all results to the 'output' directory

### Web UI

The project now includes a web-based user interface built with Streamlit, allowing for interactive data analysis:

```bash
python app.py web
```

Or simply:

```bash
python app.py
```

The web UI provides:
- Multiple data source options (cached file, database, or CSV upload)
- Step-by-step processing controls
- Interactive visualizations
- Tabbed interface for exploring different analysis results
- Data export functionality

#### Web UI Features

1. **Data Source Selection**: Choose between loading from cached files, fetching from the database, or uploading your own CSV file.
2. **Processing Steps**: Run the entire analysis pipeline or execute individual steps as needed.
3. **Interactive Visualizations**: Explore price trends, monthly averages, and day-of-week patterns.
4. **Results Tabs**: Navigate between different analysis results including:
   - Original Data
   - Extrapolated Data
   - Improved Matches
   - Summary Statistics
   - Event Analysis
   - Visualizations
5. **Export Functionality**: Export analysis results to CSV files for further processing.

#### Database Connection

The application includes robust handling for database connection issues:
- Attempts to connect to the PostgreSQL database with proper error handling
- Falls back to generating sample data when the database connection fails
- Provides clear error messages to help diagnose connection issues

## Analysis of Results

The implementation provides detailed output that allows for:
- Comparing naive vs. improved date matching
- Analyzing how different factors (seasonality, DOW, events) affect prices
- Identifying patterns in price variations across properties and time periods

The Excel output makes it easy to filter and sort the data for further analysis.
