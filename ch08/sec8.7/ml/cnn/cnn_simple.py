import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

# CIFAR-10 class names
class_names = ['airplane', 'automobile', 'bird', 'cat', 'deer', 
               'dog', 'frog', 'horse', 'ship', 'truck']

def create_model():
    """Create and compile the CNN model"""
    model = keras.Sequential([
        # First convolutional block
        layers.Conv2D(32, (3, 3), activation='relu', input_shape=(32, 32, 3)),
        layers.BatchNormalization(),
        layers.Conv2D(32, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Second convolutional block
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.BatchNormalization(),
        layers.Conv2D(64, (3, 3), activation='relu'),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Third convolutional block
        layers.Conv2D(128, (3, 3), activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.25),
        
        # Dense layers
        layers.Flatten(),
        layers.Dense(512, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        layers.Dense(10, activation='softmax')
    ])
    
    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    return model

def train_or_load_model():
    """Train a new model or load existing one"""
    model_path = 'cifar10_model.h5'
    
    if os.path.exists(model_path):
        print("Loading existing model...")
        model = keras.models.load_model(model_path)
    else:
        print("Training new model...")
        # Load and preprocess CIFAR-10 data
        (x_train, y_train), (x_test, y_test) = keras.datasets.cifar10.load_data()
        
        x_train = x_train.astype('float32') / 255.0
        x_test = x_test.astype('float32') / 255.0
        
        y_train = keras.utils.to_categorical(y_train, 10)
        y_test = keras.utils.to_categorical(y_test, 10)
        
        # Create and train model
        model = create_model()
        
        # Data augmentation
        datagen = keras.preprocessing.image.ImageDataGenerator(
            rotation_range=15,
            width_shift_range=0.1,
            height_shift_range=0.1,
            horizontal_flip=True,
            zoom_range=0.1
        )
        datagen.fit(x_train)
        
        # Callbacks
        callbacks = [
            keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
            keras.callbacks.ReduceLROnPlateau(factor=0.2, patience=5, min_lr=0.0001)
        ]
        
        # Train
        history = model.fit(
            datagen.flow(x_train, y_train, batch_size=32),
            steps_per_epoch=len(x_train) // 32,
            epochs=50,
            validation_data=(x_test, y_test),
            callbacks=callbacks,
            verbose=1
        )
        
        # Save model
        model.save(model_path)
        print(f"Model saved to {model_path}")
        
        # Evaluate
        test_loss, test_accuracy = model.evaluate(x_test, y_test, verbose=0)
        print(f"Test accuracy: {test_accuracy:.4f}")
    
    return model

def preprocess_image(image_path):
    """Load and preprocess a custom image for prediction"""
    try:
        # Load image
        img = Image.open(image_path)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to 32x32 (CIFAR-10 size)
        img = img.resize((32, 32), Image.Resampling.LANCZOS)
        
        # Convert to numpy array and normalize
        img_array = np.array(img).astype('float32') / 255.0
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array, img
    
    except Exception as e:
        print(f"Error loading image: {e}")
        return None, None

def create_prediction_image(original_img, processed_img, predictions, image_name):
    """Create a combined image showing original, processed, and predictions using Pillow"""
    # Resize original for display (max 300px width)
    display_original = original_img.copy()
    if display_original.width > 300:
        ratio = 300 / display_original.width
        new_height = int(display_original.height * ratio)
        display_original = display_original.resize((300, new_height), Image.Resampling.LANCZOS)
    
    # Resize processed image for display (scale up from 32x32)
    processed_pil = Image.fromarray((processed_img[0] * 255).astype(np.uint8))
    processed_display = processed_pil.resize((150, 150), Image.Resampling.NEAREST)
    
    # Create combined image
    total_width = display_original.width + processed_display.width + 20
    max_height = max(display_original.height, processed_display.height) + 200
    
    combined = Image.new('RGB', (total_width, max_height), 'white')
    
    # Paste images
    combined.paste(display_original, (0, 0))
    combined.paste(processed_display, (display_original.width + 10, 0))
    
    # Add text
    draw = ImageDraw.Draw(combined)
    
    try:
        # Try to use a default font
        font = ImageFont.truetype("arial.ttf", 16)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except:
        # Fall back to default font
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Add labels
    draw.text((display_original.width//2 - 40, display_original.height + 10), 
              "Original", fill='black', font=font)
    draw.text((display_original.width + processed_display.width//2 - 30, processed_display.height + 10), 
              "32x32", fill='black', font=font)
    
    # Add predictions text
    y_start = max(display_original.height, processed_display.height) + 50
    draw.text((10, y_start), f"Predictions for {image_name}:", fill='black', font=font)
    
    for i, (class_name, prob) in enumerate(predictions[:3]):
        y_pos = y_start + 30 + (i * 25)
        confidence = prob * 100
        text = f"{i+1}. {class_name}: {confidence:.2f}%"
        draw.text((10, y_pos), text, fill='black', font=small_font)
    
    return combined

def predict_image(model, image_path, save_result=False, show_predictions=True):
    """Predict the class of a custom image"""
    # Preprocess image
    processed_img, original_img = preprocess_image(image_path)
    
    if processed_img is None:
        return None
    
    # Make prediction
    predictions = model.predict(processed_img, verbose=0)
    predicted_probs = predictions[0]
    
    # Get top 3 predictions
    top_indices = np.argsort(predicted_probs)[::-1][:3]
    predictions_list = [(class_names[idx], predicted_probs[idx]) for idx in top_indices]
    
    # Display results
    if show_predictions:
        print(f"\nPredictions for {os.path.basename(image_path)}:")
        print("-" * 40)
        
        for i, (class_name, prob) in enumerate(predictions_list):
            confidence = prob * 100
            print(f"{i+1}. {class_name}: {confidence:.2f}%")
    
    # Create and save combined image
    if save_result:
        combined_img = create_prediction_image(
            original_img, processed_img, predictions_list, os.path.basename(image_path)
        )
        output_path = f"prediction_{os.path.splitext(os.path.basename(image_path))[0]}.png"
        combined_img.save(output_path)
        print(f"Prediction image saved as: {output_path}")
    
    return {
        'predictions': predictions_list,
        'all_probabilities': dict(zip(class_names, predicted_probs))
    }

def predict_multiple_images(model, image_paths, save_results=False):
    """Predict multiple images at once"""
    results = []
    
    for image_path in image_paths:
        if os.path.exists(image_path):
            result = predict_image(model, image_path, save_result=save_results, show_predictions=True)
            if result:
                results.append({
                    'image_path': image_path,
                    'top_prediction': result['predictions'][0],
                    'all_predictions': result['predictions']
                })
        else:
            print(f"Image not found: {image_path}")
    
    return results

# Main execution
if __name__ == "__main__":
    print("CIFAR-10 Image Classifier")
    print("=" * 50)
    
    # Load or train model
    model = train_or_load_model()
    
    # Example usage - replace with your image paths
    print("\nExample usage:")
    print("1. Single image prediction:")
    
    # Example image paths (replace with your actual image paths)
    example_images = [
        "images/cat.jpg",
        "images/dog.jpg",
        "images/airplane.jpg",
        "images/ship.jpg"]
    
    print("# To predict a single image:")
    print("result = predict_image(model, 'path/to/your/image.jpg')")
    print()
    print("# To predict multiple images:")
    print("results = predict_multiple_images(model, ['image1.jpg', 'image2.jpg'])")
    print()
    
    # If you have actual images, uncomment and modify these lines:
    # result = predict_image(model, "your_image.jpg")
    # results = predict_multiple_images(model, ["image1.jpg", "image2.jpg"])
    
    print("Instructions:")
    print("1. Place your images in the same directory or provide full paths")
    print("2. Call predict_image(model, 'your_image.jpg') to get predictions")
    print("3. The script will show the original image, resized version, and probability")
    print("4. It will print the top 3 most likely classes with confidence percentages")

# Additional utility function for batch processing
def batch_predict_from_folder(model, folder_path, image_extensions=('.jpg', '.jpeg', '.png', '.bmp'), save_results=False):
    """Predict all images in a folder"""
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return []
    
    image_files = []
    for file in os.listdir(folder_path):
        if file.lower().endswith(image_extensions):
            image_files.append(os.path.join(folder_path, file))
    
    if not image_files:
        print("No image files found in the folder")
        return []
    
    print(f"Found {len(image_files)} images to process...")
    results = predict_multiple_images(model, image_files, save_results=save_results)
    
    # Summary
    print(f"\nSummary of {len(results)} predictions:")
    print("-" * 50)
    for result in results:
        filename = os.path.basename(result['image_path'])
        top_class, confidence = result['top_prediction']
        print(f"{filename}: {top_class} ({confidence*100:.1f}%)")
    
    return results

# Simple function to just get predictions without visual output
def quick_predict(model, image_path):
    """Quick prediction without image creation or detailed output"""
    processed_img, _ = preprocess_image(image_path)
    if processed_img is None:
        return None
    
    predictions = model.predict(processed_img, verbose=0)
    predicted_probs = predictions[0]
    
    # Get top prediction
    top_idx = np.argmax(predicted_probs)
    return {
        'class': class_names[top_idx],
        'confidence': predicted_probs[top_idx],
        'all_probabilities': dict(zip(class_names, predicted_probs))
    }

# Remeber that thois waas trained on CIFAR-10 dataset, swith images of size 32x32.
# If you have a very detailed image, it might not work.
