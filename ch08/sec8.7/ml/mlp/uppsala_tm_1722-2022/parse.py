import pandas as pd
import numpy as np
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io

def parse_temperature_data(filename):
    """
    Parse temperature data from the Uppsala format.
    
    Expected format:
    Column 1-3: Year, month, day
    Column 4: Daily average temperature (°C)
    Column 5: Urban-corrected temperature (°C) 
    Column 6: Data source ID
    """
    
    # Read the data (assuming space-separated)
    data = []
    
    with open(filename, 'r') as file:
        for line in file:
            # Skip empty lines or comments
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Split by whitespace
            parts = line.split()
            if len(parts) >= 6:
                try:
                    year = int(parts[0])
                    month = int(parts[1])
                    day = int(parts[2])
                    temp_raw = float(parts[3])
                    temp_corrected = float(parts[4])
                    data_id = int(parts[5])
                    
                    data.append([year, month, day, temp_raw, temp_corrected, data_id])
                except ValueError:
                    # Skip lines with invalid data
                    continue
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=[
        'year', 'month', 'day', 'temp_raw', 'temp_corrected', 'data_id'
    ])
    
    # Create proper datetime index
    df['date'] = pd.to_datetime(df[['year', 'month', 'day']])
    
    # Add useful time features
    df['day_of_year'] = df['date'].dt.dayofyear
    df['decade'] = (df['year'] // 10) * 10
    df['season'] = df['month'].map({12: 'Winter', 1: 'Winter', 2: 'Winter',
                                    3: 'Spring', 4: 'Spring', 5: 'Spring',
                                    6: 'Summer', 7: 'Summer', 8: 'Summer',
                                    9: 'Autumn', 10: 'Autumn', 11: 'Autumn'})
    
    return df

def create_features_for_ml(df, use_corrected_temp=True):
    """
    Create features suitable for machine learning from the temperature data.
    
    Parameters:
    df: DataFrame from parse_temperature_data()
    use_corrected_temp: Whether to use urban-corrected temperatures
    
    Returns:
    X: Feature matrix
    y: Target values (temperatures)
    feature_names: Names of features
    """
    
    # Choose temperature column
    temp_col = 'temp_corrected' if use_corrected_temp else 'temp_raw'
    
    # Create features
    features = pd.DataFrame({
        'year': df['year'],
        'month': df['month'],
        'day_of_year': df['day_of_year'],
        'data_source': df['data_id']
    })
    
    # Add cyclical features for seasonality
    features['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    features['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    features['day_sin'] = np.sin(2 * np.pi * df['day_of_year'] / 365.25)
    features['day_cos'] = np.cos(2 * np.pi * df['day_of_year'] / 365.25)
    
    # Normalize year to start from 0
    features['year_norm'] = features['year'] - features['year'].min()
    
    X = features.values
    y = df[temp_col].values
    feature_names = features.columns.tolist()
    
    return X, y, feature_names

def analyze_data(df):
    """
    Provide basic analysis of the temperature data.
    """
    print("Dataset Overview:")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Total records: {len(df):,}")
    print(f"Years covered: {df['year'].max() - df['year'].min() + 1}")
    print()
    
    print("Data Sources:")
    source_names = {1: 'Uppsala', 2: 'Risinge', 3: 'Betna', 
                   4: 'Linköping', 5: 'Stockholm', 6: 'Interpolated'}
    for data_id in sorted(df['data_id'].unique()):
        count = (df['data_id'] == data_id).sum()
        print(f"  {data_id}: {source_names.get(data_id, 'Unknown')} - {count:,} records")
    print()
    
    print("Temperature Statistics:")
    print("Raw temperatures:")
    print(f"  Mean: {df['temp_raw'].mean():.2f}°C")
    print(f"  Range: {df['temp_raw'].min():.2f}°C to {df['temp_raw'].max():.2f}°C")
    print("Corrected temperatures:")
    print(f"  Mean: {df['temp_corrected'].mean():.2f}°C")
    print(f"  Range: {df['temp_corrected'].min():.2f}°C to {df['temp_corrected'].max():.2f}°C")
    print()
    
    # Check for missing dates
    date_range = pd.date_range(df['date'].min(), df['date'].max(), freq='D')
    missing_dates = len(date_range) - len(df)
    if missing_dates > 0:
        print(f"Missing dates: {missing_dates:,} days")
    else:
        print("No missing dates detected")

def plot_temperature_overview(df):
    """
    Create overview plots of the temperature data using Pillow.
    """
    # Set up the canvas
    width, height = 1200, 800
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 12)
        title_font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
    
    # Define plot areas with more space for labels (x, y, width, height)
    plots = {
        'timeseries': (80, 50, 470, 150),  # Moved right and made narrower to avoid collisions
        'seasonal': (600, 50, 300, 150),
        'decadal': (80, 250, 470, 150),    # Moved right to match timeseries
        'sources': (600, 250, 300, 150)
    }
    
    # Plot 1: Time series (simplified - show trend line)
    ts_area = plots['timeseries']
    draw.rectangle([ts_area[0], ts_area[1], ts_area[0] + ts_area[2], ts_area[1] + ts_area[3]], 
                   outline='black', width=2)
    draw.text((ts_area[0] + 10, ts_area[1] - 25), "Daily Temperature Time Series (1722-2022)", 
              font=title_font, fill='black')
    
    # Get yearly averages for cleaner visualization
    yearly_avg = df.groupby('year')['temp_corrected'].mean()
    years = yearly_avg.index.values
    temps = yearly_avg.values
    
    # Normalize to plot area
    x_min, x_max = years.min(), years.max()
    y_min, y_max = temps.min(), temps.max()
    
    # Add some padding
    y_range = y_max - y_min
    y_min -= y_range * 0.1
    y_max += y_range * 0.1
    
    # Convert to pixel coordinates
    def to_pixel_coords(x_val, y_val, plot_area):
        px = plot_area[0] + int((x_val - x_min) / (x_max - x_min) * plot_area[2])
        py = plot_area[1] + plot_area[3] - int((y_val - y_min) / (y_max - y_min) * plot_area[3])
        return px, py
    
    # Draw temperature trend line
    prev_point = None
    for year, temp in zip(years[::10], temps[::10]):  # Sample every 10 years for cleaner plot
        current_point = to_pixel_coords(year, temp, ts_area)
        if prev_point:
            draw.line([prev_point, current_point], fill='blue', width=2)
        prev_point = current_point
    
    # Add axes labels with better positioning
    draw.text((ts_area[0], ts_area[1] + ts_area[3] + 5), f"Year: {int(x_min)} - {int(x_max)}", 
              font=font, fill='black')
    # Y-axis labels positioned further left to avoid collision
    draw.text((ts_area[0] - 70, ts_area[1] + ts_area[3]), f"{y_min:.1f}°C", 
              font=font, fill='black')
    draw.text((ts_area[0] - 70, ts_area[1]), f"{y_max:.1f}°C", 
              font=font, fill='black')
    
    # Plot 2: Seasonal pattern
    seas_area = plots['seasonal']
    draw.rectangle([seas_area[0], seas_area[1], seas_area[0] + seas_area[2], seas_area[1] + seas_area[3]], 
                   outline='black', width=2)
    draw.text((seas_area[0] + 10, seas_area[1] - 25), "Average Temperature by Month", 
              font=title_font, fill='black')
    
    monthly_avg = df.groupby('month')['temp_corrected'].mean()
    months = monthly_avg.index.values
    month_temps = monthly_avg.values
    
    # Normalize monthly data
    month_y_min, month_y_max = month_temps.min(), month_temps.max()
    month_y_range = month_y_max - month_y_min
    month_y_min -= month_y_range * 0.1
    month_y_max += month_y_range * 0.1
    
    # Draw monthly temperature bars
    bar_width = seas_area[2] // 12
    for i, (month, temp) in enumerate(zip(months, month_temps)):
        bar_height = int((temp - month_y_min) / (month_y_max - month_y_min) * seas_area[3])
        x = seas_area[0] + i * bar_width
        y = seas_area[1] + seas_area[3] - bar_height
        draw.rectangle([x, y, x + bar_width - 2, seas_area[1] + seas_area[3]], 
                       fill='lightblue', outline='blue')
        
        # Add month labels
        if i % 2 == 0:  # Every other month to avoid crowding
            draw.text((x, seas_area[1] + seas_area[3] + 5), str(month), 
                      font=font, fill='black')
    
    # Plot 3: Decadal trends
    dec_area = plots['decadal']
    draw.rectangle([dec_area[0], dec_area[1], dec_area[0] + dec_area[2], dec_area[1] + dec_area[3]], 
                   outline='black', width=2)
    draw.text((dec_area[0] + 10, dec_area[1] - 25), "Average Temperature by Decade", 
              font=title_font, fill='black')
    
    decadal_avg = df.groupby('decade')['temp_corrected'].mean()
    decades = decadal_avg.index.values
    decade_temps = decadal_avg.values
    
    # Normalize decadal data
    dec_y_min, dec_y_max = decade_temps.min(), decade_temps.max()
    dec_y_range = dec_y_max - dec_y_min
    dec_y_min -= dec_y_range * 0.1
    dec_y_max += dec_y_range * 0.1
    
    # Draw decadal bars
    bar_width = dec_area[2] // len(decades)
    for i, (decade, temp) in enumerate(zip(decades, decade_temps)):
        bar_height = int((temp - dec_y_min) / (dec_y_max - dec_y_min) * dec_area[3])
        x = dec_area[0] + i * bar_width
        y = dec_area[1] + dec_area[3] - bar_height
        draw.rectangle([x, y, x + bar_width - 2, dec_area[1] + dec_area[3]], 
                       fill='lightgreen', outline='green')
        
        # Add decade labels (every 5th to avoid crowding)
        if i % 5 == 0:
            draw.text((x, dec_area[1] + dec_area[3] + 5), str(int(decade)), 
                      font=font, fill='black')
    
    # Plot 4: Data sources summary
    src_area = plots['sources']
    draw.rectangle([src_area[0], src_area[1], src_area[0] + src_area[2], src_area[1] + src_area[3]], 
                   outline='black', width=2)
    draw.text((src_area[0] + 10, src_area[1] - 25), "Data Sources Distribution", 
              font=title_font, fill='black')
    
    # Count data sources
    source_counts = df['data_id'].value_counts().sort_index()
    source_names = {1: 'Uppsala', 2: 'Risinge', 3: 'Betna', 
                   4: 'Linköping', 5: 'Stockholm', 6: 'Interpolated'}
    
    # Draw source information as text
    y_offset = 0
    for data_id, count in source_counts.items():
        name = source_names.get(data_id, f'Source {data_id}')
        percentage = (count / len(df)) * 100
        text = f"{data_id}: {name} ({percentage:.1f}%)"
        draw.text((src_area[0] + 10, src_area[1] + 20 + y_offset), text, 
                  font=font, fill='black')
        y_offset += 20
    
    # Add overall statistics
    stats_text = [
        f"Total records: {len(df):,}",
        f"Date range: {df['year'].min()}-{df['year'].max()}",
        f"Avg temp: {df['temp_corrected'].mean():.2f}°C",
        f"Temp range: {df['temp_corrected'].min():.1f} to {df['temp_corrected'].max():.1f}°C"
    ]
    
    for i, text in enumerate(stats_text):
        draw.text((src_area[0] + 140, src_area[1] + 20 + i * 15), text, 
                  font=font, fill='navy')
    
    # Add title
    draw.text((width//2 - 150, 10), "Uppsala Temperature Data Analysis (1722-2022)", 
              font=title_font, fill='darkblue')
    
    # Save or display the image
    img.save("temperature_overview.png")
    print("Temperature overview plot saved as 'temperature_overview.png'")
    
    # Optionally display the image
    img.show()
    
    return img

# Example usage:
if __name__ == "__main__":
    filename = "uppsala_tm_1722-2022.dat"
    
    try:
        # Parse the data
        df = parse_temperature_data(filename)
        
        # Analyze the data
        analyze_data(df)
        
        # Create visualizations
        plot_temperature_overview(df)
        
        # Prepare features for ML
        X, y, feature_names = create_features_for_ml(df, use_corrected_temp=True)
        
        print("Features prepared for ML:")
        print(f"Feature matrix shape: {X.shape}")
        print(f"Target vector shape: {y.shape}")
        print(f"Features: {feature_names}")
        
    except FileNotFoundError:
        print(f"File '{filename}' not found. Please update the filename.")
        print("Sample data structure expected:")
        print("1722  1 12   1.9   1.8 1")
        print("1722  1 13   2.3   2.2 1")
        print("...")
