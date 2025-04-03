# Nightly Price Analysis

This project implements the requirements for analyzing and extrapolating nightly rental price data for multiple properties.

[**Online DEMO**](https://nightlyprices-gwesa4temvgrsxvvsmhh6j.streamlit.app/)

## Overview

The implementation handles two main tasks:

1. **Extrapolating Prices Backward**: Fills in daily prices from January 1, 2024, through September 2, 2024, using data from the corresponding dates in 2025.

2. **Finding Improved "-1 Year" Matches**: Implements a better approach to matching future dates with corresponding dates from the previous year, respecting weekday and event alignments.

## Implementation Details

### Price Extrapolation Approach

For extrapolating prices back to January 1, 2024:

1. **Base Price**: Uses the same base price as in the existing data for each property.
2. **Seasonality**: Uses the seasonality factor from the corresponding "+1 year" date.
3. **Event**: Uses the event factor from the corresponding "+1 year" date.
4. **Day-of-Week (DOW)**: Averages DOW values from dates with the same weekday in a 14-days range from the "+1 year" date.

### Improved "-1 Year" Matches Approach

For finding better matches between future dates and past dates:

1. **Event Alignment**: When a future date has an event factor > 1.0, the algorithm prioritizes finding a past date with a similar event factor, even if the weekday differs.
2. **Weekday Alignment**: When a future date has no special event, the algorithm finds the nearest date with the same weekday and no event.
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

The project includes a web-based user interface built with Streamlit, allowing for interactive data analysis:

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





