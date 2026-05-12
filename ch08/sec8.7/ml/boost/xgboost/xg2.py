import xgboost as xgb
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score
from PIL import Image, ImageDraw, ImageFont
import os

# Generate synthetic dataset
X, y = make_classification(n_samples=1000, n_features=20, n_informative=15, random_state=42)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create XGBoost model
model = xgb.XGBClassifier(random_state=42)

# Perform 5-fold cross-validation
cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
print(f"Cross-validation accuracy: {np.mean(cv_scores):.2f} (+/- {np.std(cv_scores) * 2:.2f})")

# Simple grid search for hyperparameter tuning
param_grid = {
    'n_estimators': [50, 100],
    'max_depth': [3, 5],
    'learning_rate': [0.01, 0.1]
}
grid_search = GridSearchCV(model, param_grid, cv=3, scoring='accuracy', n_jobs=-1)
grid_search.fit(X_train, y_train)

# Best model from grid search
best_model = grid_search.best_estimator_
print(f"Best parameters: {grid_search.best_params_}")

# Train best model
best_model.fit(X_train, y_train)

# Make predictions
y_pred = best_model.predict(X_test)

# Evaluate accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"Test accuracy: {accuracy:.2f}")

# Get feature importance (using 'gain')
feature_importance = best_model.get_booster().get_score(importance_type='gain')
feature_names = [f"f{i}" for i in range(X.shape[1])]  # Synthetic feature names
importance_scores = [feature_importance.get(f"f{i}", 0) for i in range(len(feature_names))]

# Normalize importance scores for visualization (scale to max bar length)
max_length = 400  # Maximum bar length in pixels
max_importance = max(importance_scores) if max(importance_scores) > 0 else 1
normalized_scores = [score / max_importance * max_length for score in importance_scores]

print("\nFeature Importance Details (Top 10):")
print(f"{'Feature':<10} {'Raw Gain':>12} {'Normalized Score':>15} {'Image Text Value':>15}")
print("-" * 50)
top_features = sorted(zip(feature_names, importance_scores, normalized_scores), 
                      key=lambda x: x[1], reverse=True)[:10]
for feature, raw_score, norm_score in top_features:
    image_text_value = round(raw_score, 2)  # Match image's 2-decimal formatting
    print(f"{feature:<10} {raw_score:>12.4f} {norm_score:>15.4f} {image_text_value:>15.2f}")

# Create image with Pillow (same as before)
image_width = 600
image_height = len(feature_names) * 50 + 100
image = Image.new('RGB', (image_width, image_height), 'white')
draw = ImageDraw.Draw(image)

# Try to load a font
try:
    font = ImageFont.truetype("arial.ttf", 20)
except:
    font = ImageFont.load_default()

# Draw title
draw.text((10, 10), "Feature Importance (Gain)", fill='black', font=font)

# Draw bars and labels for top 10 features
bar_height = 30
y_offset = 50
for i, (feature, _, norm_score) in enumerate(top_features):
    draw.rectangle(
        [(100, y_offset + i * 50), (100 + norm_score, y_offset + i * 50 + bar_height)],
        fill='blue'
    )
    draw.text((10, y_offset + i * 50 + 5), feature, fill='black', font=font)
    draw.text((110 + norm_score, y_offset + i * 50 + 5), 
              f"{feature_importance[feature]:.2f}", fill='black', font=font)

# Save and display image
image.save('feature_importance.png')
image.show()
print("\nFeature importance image saved as 'feature_importance.png'")