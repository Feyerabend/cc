import tensorflow as tf
from tensorflow import keras
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import sys

# CIFAR-10 class names
class_names = ['airplane', 'automobile', 'bird', 'cat', 'deer', 
               'dog', 'frog', 'horse', 'ship', 'truck']

def load_model(model_path='cifar10_model.h5'):
    """Load the trained CIFAR-10 model"""
    if not os.path.exists(model_path):
        print(f"Model file not found: {model_path}")
        print("Please make sure you have trained the model first using the training script.")
        return None
    
    try:
        print(f"Loading model from {model_path}...")
        model = keras.models.load_model(model_path)
        print("Model loaded successfully!")
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

def preprocess_image(image_path):
    """Load and preprocess a custom image for prediction"""
    try:
        # Load image
        img = Image.open(image_path)
        print(f"Original image size: {img.size}")
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
            print("Converted image to RGB")
        
        # Resize to 32x32 (CIFAR-10 size)
        img_resized = img.resize((32, 32), Image.Resampling.LANCZOS)
        
        # Convert to numpy array and normalize
        img_array = np.array(img_resized).astype('float32') / 255.0
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array, img, img_resized
    
    except Exception as e:
        print(f"Error loading image: {e}")
        return None, None, None

def predict_single_image(model, image_path, verbose=True):
    """Predict the class of a single image"""
    # Preprocess image
    processed_img, original_img, resized_img = preprocess_image(image_path)
    
    if processed_img is None:
        return None
    
    # Make prediction
    print("Making prediction...")
    predictions = model.predict(processed_img, verbose=0)
    predicted_probs = predictions[0]
    
    # Get results
    top_idx = np.argmax(predicted_probs)
    top_confidence = predicted_probs[top_idx]
    
    # Get top 3 predictions
    top_indices = np.argsort(predicted_probs)[::-1][:3]
    
    if verbose:
        print(f"\nResults for {os.path.basename(image_path)}:")
        print("=" * 50)
        print(f"Top prediction: {class_names[top_idx]} ({top_confidence*100:.2f}%)")
        print("\nTop 3 predictions:")
        for i, idx in enumerate(top_indices):
            confidence = predicted_probs[idx] * 100
            print(f"  {i+1}. {class_names[idx]}: {confidence:.2f}%")
    
    return {
        'top_class': class_names[top_idx],
        'top_confidence': top_confidence,
        'top_3': [(class_names[idx], predicted_probs[idx]) for idx in top_indices],
        'all_probabilities': dict(zip(class_names, predicted_probs)),
        'original_image': original_img,
        'resized_image': resized_img
    }

def create_result_image(result, image_path, save_path=None):
    """Create a visual result showing the prediction"""
    if result is None:
        return None
    
    original = result['original_image']
    resized = result['resized_image']
    
    # Create display versions
    display_original = original.copy()
    if display_original.width > 300:
        ratio = 300 / display_original.width
        new_height = int(display_original.height * ratio)
        display_original = display_original.resize((300, new_height), Image.Resampling.LANCZOS)
    
    # Scale up the 32x32 image for better visibility
    display_resized = resized.resize((150, 150), Image.Resampling.NEAREST)
    
    # Create combined image
    padding = 20
    text_height = 150
    total_width = display_original.width + display_resized.width + padding * 3
    total_height = max(display_original.height, display_resized.height) + text_height + padding * 2
    
    combined = Image.new('RGB', (total_width, total_height), 'white')
    
    # Paste images
    combined.paste(display_original, (padding, padding))
    combined.paste(display_resized, (display_original.width + padding * 2, padding))
    
    # Add text
    draw = ImageDraw.Draw(combined)
    
    try:
        font_large = ImageFont.truetype("arial.ttf", 18)
        font_medium = ImageFont.truetype("arial.ttf", 14)
        font_small = ImageFont.truetype("arial.ttf", 12)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Image labels
    draw.text((padding + display_original.width//2 - 40, display_original.height + padding + 10), 
              "Original", fill='black', font=font_medium)
    draw.text((display_original.width + padding * 2 + 50, display_resized.height + padding + 10), 
              "32x32", fill='black', font=font_medium)
    
    # Prediction results
    y_start = max(display_original.height, display_resized.height) + padding + 50
    
    # Title
    filename = os.path.basename(image_path)
    draw.text((padding, y_start), f"Predictions for: {filename}", fill='black', font=font_large)
    
    # Top prediction (highlighted)
    top_class = result['top_class']
    top_conf = result['top_confidence'] * 100
    draw.text((padding, y_start + 30), f"→ {top_class}: {top_conf:.1f}%", fill='red', font=font_medium)
    
    # Other predictions
    for i, (class_name, prob) in enumerate(result['top_3'][1:3]):
        y_pos = y_start + 55 + (i * 20)
        confidence = prob * 100
        draw.text((padding, y_pos), f"  {class_name}: {confidence:.1f}%", fill='gray', font=font_small)
    
    # Save if path provided
    if save_path:
        combined.save(save_path)
        print(f"Result image saved as: {save_path}")
    
    return combined

def batch_predict(model, image_list, save_images=False):
    """Predict multiple images"""
    results = []
    
    print(f"Processing {len(image_list)} images...")
    print("=" * 50)
    
    for i, image_path in enumerate(image_list, 1):
        if not os.path.exists(image_path):
            print(f"{i}. Skipping {image_path} - file not found")
            continue
            
        print(f"\n{i}. Processing {os.path.basename(image_path)}...")
        
        result = predict_single_image(model, image_path, verbose=False)
        if result:
            results.append({
                'image_path': image_path,
                'result': result
            })
            
            # Print quick result
            top_class = result['top_class']
            confidence = result['top_confidence'] * 100
            print(f"   → {top_class} ({confidence:.1f}%)")
            
            # Save result image if requested
            if save_images:
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                save_path = f"result_{base_name}.png"
                create_result_image(result, image_path, save_path)
    
    return results

def predict_folder(model, folder_path, extensions=('.jpg', '.jpeg', '.png', '.bmp'), save_images=False):
    """Predict all images in a folder"""
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return []
    
    # Find all image files
    image_files = []
    for file in os.listdir(folder_path):
        if file.lower().endswith(extensions):
            image_files.append(os.path.join(folder_path, file))
    
    if not image_files:
        print(f"No image files found in {folder_path}")
        return []
    
    print(f"Found {len(image_files)} images in {folder_path}")
    return batch_predict(model, image_files, save_images)

def main():
    """Main function for command line usage"""
    print("CIFAR-10 Image Classifier - Model User")
    print("=" * 50)
    
    # Load model
    model = load_model()
    if model is None:
        return
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python model_user.py <image_path>           - Predict single image")
        print("  python model_user.py <folder_path> --folder - Predict all images in folder")
        print("  python model_user.py <image_path> --save    - Predict and save result image")
        print("\nExample:")
        print("  python model_user.py images/cat.jpg")
        print("  python model_user.py images/ --folder")
        print("  python model_user.py my_dog.jpg --save")
        return
    
    path = sys.argv[1]
    save_images = '--save' in sys.argv
    is_folder = '--folder' in sys.argv
    
    if is_folder:
        # Process folder
        results = predict_folder(model, path, save_images=save_images)
        
        # Summary
        if results:
            print(f"\n" + "=" * 50)
            print("SUMMARY:")
            print("=" * 50)
            for item in results:
                filename = os.path.basename(item['image_path'])
                result = item['result']
                print(f"{filename}: {result['top_class']} ({result['top_confidence']*100:.1f}%)")
    else:
        # Process single image
        result = predict_single_image(model, path)
        if result and save_images:
            base_name = os.path.splitext(os.path.basename(path))[0]
            save_path = f"result_{base_name}.png"
            create_result_image(result, path, save_path)

# Example usage functions
def example_usage():
    """Show example usage"""
    print("\nExample usage in Python:")
    print("=" * 30)
    print("""
# Load model
model = load_model('cifar10_model.h5')

# Predict single image
result = predict_single_image(model, 'my_image.jpg')

# Create and save result image
create_result_image(result, 'my_image.jpg', 'result.png')

# Predict multiple images
image_list = ['cat.jpg', 'dog.jpg', 'plane.jpg']
results = batch_predict(model, image_list, save_images=True)

# Predict all images in a folder
results = predict_folder(model, 'my_images/', save_images=True)
""")

if __name__ == "__main__":
    main()