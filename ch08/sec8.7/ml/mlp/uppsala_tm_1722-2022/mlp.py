import tensorflow as tf
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.linear_model import LinearRegression
import io
import os

# Temperature data parser functions
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

# Machine Learning functions
def build_temperature_mlp(input_dim, hidden_layers=[64, 32, 16]):
    """
    Build MLP for temperature prediction.
    
    Parameters:
    input_dim: Number of input features
    hidden_layers: List of neurons in each hidden layer
    """
    model = tf.keras.Sequential()
    
    # Input layer
    model.add(tf.keras.layers.Input(shape=(input_dim,)))
    
    # Hidden layers
    for i, units in enumerate(hidden_layers):
        model.add(tf.keras.layers.Dense(units, activation='relu'))
        # Add dropout for regularization (except last hidden layer)
        if i < len(hidden_layers) - 1:
            model.add(tf.keras.layers.Dropout(0.2))
    
    # Output layer
    model.add(tf.keras.layers.Dense(1, activation='linear'))
    
    return model

def train_and_evaluate_models(X, y, feature_names, test_size=0.2):
    """
    Train both MLP and Linear Regression models and compare them.
    """
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, shuffle=True
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"Training set size: {len(X_train):,}")
    print(f"Test set size: {len(X_test):,}")
    print(f"Features: {len(feature_names)}")
    print()
    
    # Build and train MLP
    print("Training MLP...")
    mlp_model = build_temperature_mlp(X_train_scaled.shape[1])
    
    mlp_model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='mse',
        metrics=['mae']
    )
    
    # Train with early stopping
    early_stopping = tf.keras.callbacks.EarlyStopping(
        monitor='val_loss', patience=15, restore_best_weights=True
    )
    
    mlp_history = mlp_model.fit(
        X_train_scaled, y_train,
        validation_split=0.2,
        epochs=100,
        batch_size=256,
        callbacks=[early_stopping],
        verbose=1
    )
    
    # MLP predictions
    mlp_pred_test = mlp_model.predict(X_test_scaled).flatten()
    mlp_pred_train = mlp_model.predict(X_train_scaled).flatten()
    
    # Train Linear Regression for comparison
    print("\nTraining Linear Regression...")
    lr_model = LinearRegression()
    lr_model.fit(X_train_scaled, y_train)
    
    lr_pred_test = lr_model.predict(X_test_scaled)
    lr_pred_train = lr_model.predict(X_train_scaled)
    
    # Calculate metrics
    def calculate_metrics(y_true, y_pred, model_name, dataset_name):
        mse = mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        
        print(f"{model_name} ({dataset_name}):")
        print(f"  MSE: {mse:.4f}")
        print(f"  MAE: {mae:.4f}")
        print(f"  R²:  {r2:.4f}")
        return mse, mae, r2
    
    print("\n" + "="*50)
    print("MODEL COMPARISON")
    print("="*50)
    
    # Test set performance
    mlp_mse_test, mlp_mae_test, mlp_r2_test = calculate_metrics(
        y_test, mlp_pred_test, "MLP", "Test"
    )
    lr_mse_test, lr_mae_test, lr_r2_test = calculate_metrics(
        y_test, lr_pred_test, "Linear Regression", "Test"
    )
    
    print()
    
    # Training set performance (to check overfitting)
    mlp_mse_train, mlp_mae_train, mlp_r2_train = calculate_metrics(
        y_train, mlp_pred_train, "MLP", "Train"
    )
    lr_mse_train, lr_mae_train, lr_r2_train = calculate_metrics(
        y_train, lr_pred_train, "Linear Regression", "Train"
    )
    
    # Feature importance (for Linear Regression)
    print(f"\nTop 5 Most Important Features (Linear Regression):")
    feature_importance = np.abs(lr_model.coef_)
    top_features = np.argsort(feature_importance)[-5:][::-1]
    for i, idx in enumerate(top_features):
        print(f"  {i+1}. {feature_names[idx]}: {lr_model.coef_[idx]:.4f}")
    
    return {
        'mlp_model': mlp_model,
        'lr_model': lr_model,
        'scaler': scaler,
        'history': mlp_history,
        'predictions': {
            'mlp_test': mlp_pred_test,
            'lr_test': lr_pred_test,
            'y_test': y_test
        },
        'metrics': {
            'mlp': {'test_r2': mlp_r2_test, 'test_mae': mlp_mae_test},
            'lr': {'test_r2': lr_r2_test, 'test_mae': lr_mae_test}
        }
    }

# Pillow-based plotting functions
def get_default_font():
    """Try to get a default font, fallback to default if not available."""
    try:
        # Try to use a common system font
        return ImageFont.truetype("arial.ttf", 12)
    except:
        try:
            return ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 12)
        except:
            return ImageFont.load_default()

def normalize_data(data, target_min=50, target_max=350):
    """Normalize data to target range for plotting."""
    data_min, data_max = np.min(data), np.max(data)
    if data_max == data_min:
        return np.full_like(data, (target_min + target_max) / 2)
    return target_min + (data - data_min) * (target_max - target_min) / (data_max - data_min)

def create_scatter_plot(x_data, y_data, title, xlabel, ylabel, width=600, height=400):
    """Create a scatter plot using Pillow."""
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    font = get_default_font()
    
    # Margins
    margin_left, margin_right = 80, 20
    margin_top, margin_bottom = 40, 60
    
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    
    # Normalize data to plot area
    x_plot = normalize_data(x_data, margin_left, margin_left + plot_width)
    y_plot = normalize_data(y_data, margin_top + plot_height, margin_top)  # Flip Y axis
    
    # Draw points
    for i in range(min(len(x_plot), 2000)):  # Limit points for performance
        x, y = int(x_plot[i]), int(y_plot[i])
        draw.ellipse([x-1, y-1, x+1, y+1], fill='blue')
    
    # Draw diagonal line (perfect prediction) - FIXED
    # Perfect prediction line should go from bottom-left to top-right
    x_min, x_max = margin_left, margin_left + plot_width
    y_max, y_min = margin_top + plot_height, margin_top  # Note: y_max is bottom, y_min is top
    draw.line([x_min, y_max, x_max, y_min], fill='red', width=2)  # Bottom-left to top-right
    
    # Draw axes
    draw.line([margin_left, margin_top, margin_left, margin_top + plot_height], fill='black', width=2)
    draw.line([margin_left, margin_top + plot_height, margin_left + plot_width, margin_top + plot_height], fill='black', width=2)
    
    # Add labels
    draw.text((width//2 - 50, 10), title, fill='black', font=font)
    draw.text((width//2 - 30, height - 20), xlabel, fill='black', font=font)
    
    # Y-axis label (rotated text approximation)
    y_label_y = height // 2
    for i, char in enumerate(ylabel):
        draw.text((10, y_label_y + i * 15), char, fill='black', font=font)
    
    # Add axis values
    x_min_val, x_max_val = np.min(x_data), np.max(x_data)
    y_min_val, y_max_val = np.min(y_data), np.max(y_data)
    
    draw.text((margin_left - 5, margin_top + plot_height + 5), f'{x_min_val:.1f}', fill='black', font=font)
    draw.text((margin_left + plot_width - 20, margin_top + plot_height + 5), f'{x_max_val:.1f}', fill='black', font=font)
    draw.text((margin_left - 40, margin_top + plot_height), f'{y_min_val:.1f}', fill='black', font=font)
    draw.text((margin_left - 40, margin_top), f'{y_max_val:.1f}', fill='black', font=font)
    
    return img

def create_line_plot(x_data, y_data, title, xlabel, ylabel, width=600, height=400):
    """Create a line plot using Pillow."""
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    font = get_default_font()
    
    # Margins
    margin_left, margin_right = 80, 20
    margin_top, margin_bottom = 40, 60
    
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    
    # Normalize data to plot area
    x_plot = normalize_data(x_data, margin_left, margin_left + plot_width)
    # FIXED: Invert the y-axis mapping so higher values appear at top, lower at bottom
    y_plot = normalize_data(y_data, margin_top, margin_top + plot_height)
    
    # Draw line
    points = [(int(x_plot[i]), int(y_plot[i])) for i in range(len(x_plot))]
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill='blue', width=2)
    
    # Draw axes
    draw.line([margin_left, margin_top, margin_left, margin_top + plot_height], fill='black', width=2)
    draw.line([margin_left, margin_top + plot_height, margin_left + plot_width, margin_top + plot_height], fill='black', width=2)
    
    # Add labels
    draw.text((width//2 - 50, 10), title, fill='black', font=font)
    draw.text((width//2 - 30, height - 20), xlabel, fill='black', font=font)
    
    # Y-axis label (rotated text approximation)
    y_label_y = height // 2
    for i, char in enumerate(ylabel):
        draw.text((10, y_label_y + i * 15), char, fill='black', font=font)
    
    # Add axis values - FIXED: Update to match the corrected y-axis
    x_min_val, x_max_val = np.min(x_data), np.max(x_data)
    y_min_val, y_max_val = np.min(y_data), np.max(y_data)
    
    # X-axis labels
    draw.text((margin_left - 5, margin_top + plot_height + 5), f'{x_min_val:.1f}', fill='black', font=font)
    draw.text((margin_left + plot_width - 20, margin_top + plot_height + 5), f'{x_max_val:.1f}', fill='black', font=font)
    
    # Y-axis labels (corrected: min at bottom, max at top)
    draw.text((margin_left - 40, margin_top + plot_height), f'{y_min_val:.4f}', fill='black', font=font)  # Bottom = min
    draw.text((margin_left - 40, margin_top), f'{y_max_val:.4f}', fill='black', font=font)  # Top = max
    
    return img

def create_bar_chart(categories, values, title, ylabel, width=400, height=300):
    """Create a bar chart using Pillow."""
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    font = get_default_font()
    
    # Margins
    margin_left, margin_right = 40, 20
    margin_top, margin_bottom = 40, 80
    
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    
    # Bar dimensions
    bar_width = plot_width // len(categories) - 10
    max_val = max(values) if max(values) > 0 else 1
    
    # Draw bars
    colors = ['blue', 'orange', 'green', 'red', 'purple']
    for i, (cat, val) in enumerate(zip(categories, values)):
        x = margin_left + i * (plot_width // len(categories))
        bar_height = int((val / max_val) * plot_height)
        y = margin_top + plot_height - bar_height
        
        color = colors[i % len(colors)]
        draw.rectangle([x, y, x + bar_width, margin_top + plot_height], fill=color)
        
        # Add value on top of bar
        draw.text((x + bar_width//4, y - 20), f'{val:.3f}', fill='black', font=font)
        
        # Add category label
        draw.text((x, margin_top + plot_height + 10), cat[:10], fill='black', font=font)
    
    # Draw axes
    draw.line([margin_left, margin_top, margin_left, margin_top + plot_height], fill='black', width=2)
    draw.line([margin_left, margin_top + plot_height, margin_left + plot_width, margin_top + plot_height], fill='black', width=2)
    
    # Add title
    draw.text((width//2 - 50, 10), title, fill='black', font=font)
    
    return img

def create_histogram(data, title, xlabel, bins=30, width=400, height=300):
    """Create a histogram using Pillow."""
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    font = get_default_font()
    
    # Calculate histogram
    hist, bin_edges = np.histogram(data, bins=bins)
    
    # Margins
    margin_left, margin_right = 40, 20
    margin_top, margin_bottom = 40, 60
    
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    
    # Draw histogram bars
    bar_width = plot_width // len(hist)
    max_count = max(hist) if max(hist) > 0 else 1
    
    for i, count in enumerate(hist):
        x = margin_left + i * bar_width
        bar_height = int((count / max_count) * plot_height)
        y = margin_top + plot_height - bar_height
        
        draw.rectangle([x, y, x + bar_width - 1, margin_top + plot_height], fill='lightblue', outline='blue')
    
    # Draw axes
    draw.line([margin_left, margin_top, margin_left, margin_top + plot_height], fill='black', width=2)
    draw.line([margin_left, margin_top + plot_height, margin_left + plot_width, margin_top + plot_height], fill='black', width=2)
    
    # Add labels
    draw.text((width//2 - 50, 10), title, fill='black', font=font)
    draw.text((width//2 - 30, height - 20), xlabel, fill='black', font=font)
    
    return img

def plot_results(results, df_sample=None):
    """
    Create and save visualization plots using Pillow.
    """
    print("Creating visualizations with Pillow...")
    
    # Create output directory
    os.makedirs('plots', exist_ok=True)
    
    # Plot 1: Training history
    history = results['history']
    epochs = range(1, len(history.history['loss']) + 1)
    train_loss_img = create_line_plot(
        epochs, history.history['loss'],
        'MLP Training Loss', 'Epoch', 'Loss (MSE)'
    )
    train_loss_img.save('plots/training_loss.png')
    
    # Plot 2: MLP Predictions vs Actual
    pred = results['predictions']
    mlp_scatter = create_scatter_plot(
        pred['y_test'], pred['mlp_test'],
        f'MLP: R² = {results["metrics"]["mlp"]["test_r2"]:.4f}',
        'Actual Temperature (°C)', 'MLP Predicted Temperature (°C)'
    )
    mlp_scatter.save('plots/mlp_predictions.png')
    
    # Plot 3: Linear Regression Predictions vs Actual
    lr_scatter = create_scatter_plot(
        pred['y_test'], pred['lr_test'],
        f'Linear Reg: R² = {results["metrics"]["lr"]["test_r2"]:.4f}',
        'Actual Temperature (°C)', 'LR Predicted Temperature (°C)'
    )
    lr_scatter.save('plots/lr_predictions.png')
    
    # Plot 4: Residuals histogram
    mlp_residuals = pred['y_test'] - pred['mlp_test']
    residuals_hist = create_histogram(
        mlp_residuals, 'MLP Residuals Distribution', 'Residuals (°C)'
    )
    residuals_hist.save('plots/residuals_histogram.png')
    
    # Plot 5: Model comparison - R² scores
    models = ['MLP', 'Linear Reg']
    r2_scores = [results['metrics']['mlp']['test_r2'], results['metrics']['lr']['test_r2']]
    r2_chart = create_bar_chart(models, r2_scores, 'Model Comparison - R²', 'R² Score')
    r2_chart.save('plots/r2_comparison.png')
    
    # Plot 6: Model comparison - MAE scores
    mae_scores = [results['metrics']['mlp']['test_mae'], results['metrics']['lr']['test_mae']]
    mae_chart = create_bar_chart(models, mae_scores, 'Model Comparison - MAE', 'MAE (°C)')
    mae_chart.save('plots/mae_comparison.png')
    
    print("Plots saved to 'plots/' directory:")
    print("  - training_loss.png")
    print("  - mlp_predictions.png")
    print("  - lr_predictions.png")
    print("  - residuals_histogram.png")
    print("  - r2_comparison.png")
    print("  - mae_comparison.png")

# Main execution
if __name__ == "__main__":
    filename = "uppsala_tm_1722-2022.dat"    
    print("Loading temperature data...")
    
    # Try to load real data, fall back to sample data if file not found
    try:
        df = parse_temperature_data(filename)
        print(f"Loaded {len(df):,} temperature records from {filename}")
    except FileNotFoundError:
        print(f"File '{filename}' not found. Creating sample data for demonstration...")
        
        # Sample data creation
        np.random.seed(42)
        dates = pd.date_range('1722-01-01', '2022-12-31', freq='D')
        n_days = len(dates)
        
        # Create realistic seasonal temperature pattern
        day_of_year = dates.dayofyear
        seasonal_temp = 8 * np.sin(2 * np.pi * (day_of_year - 80) / 365.25)
        
        # Add long-term warming trend
        years_since_start = (dates.year - 1722) / 300
        warming_trend = 1.5 * years_since_start
        
        # Add noise
        noise = np.random.normal(0, 2.5, n_days)
        
        df = pd.DataFrame({
            'year': dates.year,
            'month': dates.month,
            'day': dates.day,
            'temp_corrected': seasonal_temp + warming_trend + noise,
            'data_id': np.random.choice([1, 2, 3, 4, 5, 6], n_days),
            'date': dates,
            'day_of_year': day_of_year
        })
        
        print(f"Created {len(df):,} sample temperature records")
    
    # Create features for ML
    X, y, feature_names = create_features_for_ml(df, use_corrected_temp=True)
    
    print("\nFeatures created:")
    for i, name in enumerate(feature_names):
        print(f"  {i}: {name}")
    
    # Train and evaluate models
    results = train_and_evaluate_models(X, y, feature_names)
    
    # Create plots with Pillow
    plot_results(results, df)
    
    print("\n" + "="*50)
    print("EDUCATIONAL INSIGHTS")
    print("="*50)
    print("1. Compare MLP vs Linear Regression performance")
    print("2. Look at residuals to see what patterns each model captures")
    print("3. Check if MLP overfits (compare train vs test metrics)")
    print("4. Experiment with different MLP architectures")
    print("5. Try removing seasonal features to see impact")
    print("6. Check the 'plots/' directory for generated visualizations")