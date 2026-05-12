import csv
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def load_pca_data(filename):
    """Load PCA results from CSV"""
    training_data = []
    test_data = []
    
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pc1 = float(row['pc1'])
            pc2 = float(row['pc2'])
            point_type = row['type']
            label = row['original_label']
            
            if point_type == 'training':
                training_data.append((pc1, pc2, label))
            else:  # predicted
                test_data.append((pc1, pc2, label))
    
    return training_data, test_data

def normalize_coords(all_points, width, height, margin=50):
    """Normalize coordinates to fit in image"""
    all_x = [p[0] for p in all_points]
    all_y = [p[1] for p in all_points]
    
    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    
    # Add some padding to ranges
    x_range = max_x - min_x
    y_range = max_y - min_y
    min_x -= x_range * 0.1
    max_x += x_range * 0.1
    min_y -= y_range * 0.1
    max_y += y_range * 0.1
    
    # Scale to fit in image
    scale_x = (width - 2 * margin) / (max_x - min_x) if max_x != min_x else 1
    scale_y = (height - 2 * margin) / (max_y - min_y) if max_y != min_y else 1
    
    normalized = []
    for x, y, label in all_points:
        norm_x = (x - min_x) * scale_x + margin
        norm_y = height - ((y - min_y) * scale_y + margin)  # Flip Y axis
        normalized.append((int(norm_x), int(norm_y), label))
    
    return normalized

def create_visualization(training_data, test_data, width=800, height=600):
    """Create visualization of PCA results"""
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Combine all data for normalization
    all_points = training_data + test_data
    normalized = normalize_coords(all_points, width, height)
    
    # Split back
    norm_training = normalized[:len(training_data)]
    norm_test = normalized[len(training_data):]
    
    # Draw grid lines
    draw.line([50, height//2, width-50, height//2], fill='lightgray', width=1)  # horizontal
    draw.line([width//2, 50, width//2, height-50], fill='lightgray', width=1)   # vertical
    
    # Draw training points (larger circles)
    for x, y, label in norm_training:
        if label == 'apple':
            color = (255, 0, 0)      # red
            outline = (139, 0, 0)    # dark red
        else:  # orange
            color = (255, 165, 0)    # orange
            outline = (255, 140, 0)  # dark orange
        
        draw.ellipse([x-6, y-6, x+6, y+6], fill=color, outline=outline, width=2)
    
    # Draw test points (X marks)
    for x, y, pred_label in norm_test:
        if pred_label == 'apple':
            color = (139, 0, 0)      # dark red
        else:  # orange
            color = (255, 69, 0)     # red orange
        
        # Draw X mark
        draw.line([x-5, y-5, x+5, y+5], fill=color, width=3)
        draw.line([x-5, y+5, x+5, y-5], fill=color, width=3)
    
    # Add legend
    legend_y = 20
    draw.ellipse([20, legend_y, 32, legend_y+12], fill=(255, 0, 0), outline=(139, 0, 0))
    draw.text((40, legend_y), "Training Apples", fill='black')
    
    legend_y += 25
    draw.ellipse([20, legend_y, 32, legend_y+12], fill=(255, 165, 0), outline=(255, 140, 0))
    draw.text((40, legend_y), "Training Oranges", fill='black')
    
    legend_y += 25
    draw.line([20, legend_y+6, 32, legend_y+6], fill=(139, 0, 0), width=3)
    draw.line([26, legend_y, 26, legend_y+12], fill=(139, 0, 0), width=3)
    draw.text((40, legend_y), "Predicted Apples", fill='black')
    
    legend_y += 25
    draw.line([20, legend_y+6, 32, legend_y+6], fill=(255, 69, 0), width=3)
    draw.line([26, legend_y, 26, legend_y+12], fill=(255, 69, 0), width=3)
    draw.text((40, legend_y), "Predicted Oranges", fill='black')
    
    # Add title
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font = ImageFont.load_default()
    
    draw.text((width//2 - 100, 10), "PCA Results Visualization", fill='black', font=font)
    draw.text((width//2 - 50, height - 30), "PC1", fill='black')
    
    # Rotate text for Y axis is complex in PIL, so just use PC2
    draw.text((10, height//2 - 10), "PC2", fill='black')
    
    return img

def analyze_results(training_data, test_data):
    """Analyze the clustering results"""
    print("=== PCA Results Analysis ===")
    
    # Analyze training clusters
    apple_points = [(x, y) for x, y, label in training_data if label == 'apple']
    orange_points = [(x, y) for x, y, label in training_data if label == 'orange']
    
    apple_center = (np.mean([p[0] for p in apple_points]), np.mean([p[1] for p in apple_points]))
    orange_center = (np.mean([p[0] for p in orange_points]), np.mean([p[1] for p in orange_points]))
    
    print(f"Apple cluster center: PC1={apple_center[0]:.3f}, PC2={apple_center[1]:.3f}")
    print(f"Orange cluster center: PC1={orange_center[0]:.3f}, PC2={orange_center[1]:.3f}")
    print(f"Cluster separation: {np.sqrt((apple_center[0]-orange_center[0])**2 + (apple_center[1]-orange_center[1])**2):.3f}")
    
    # Analyze test predictions
    test_apples = [p for p in test_data if p[2] == 'apple']
    test_oranges = [p for p in test_data if p[2] == 'orange']
    
    print(f"\nTest predictions:")
    print(f"Predicted as apple: {len(test_apples)}")
    print(f"Predicted as orange: {len(test_oranges)}")
    
    return apple_center, orange_center

# Load and visualize the data
try:
    training_data, test_data = load_pca_data('pca_results.csv')
    
    # Analyze results
    apple_center, orange_center = analyze_results(training_data, test_data)
    
    # Create visualization
    img = create_visualization(training_data, test_data)
    img.save('pca_analysis.png')
    
    print(f"\nVisualization saved as 'pca_analysis.png'")
    print(f"Total training points: {len(training_data)}")
    print(f"Total test points: {len(test_data)}")
    
except FileNotFoundError:
    print("Could not find 'pca_results.csv'. Make sure the file exists in the current directory.")
except Exception as e:
    print(f"Error: {e}")