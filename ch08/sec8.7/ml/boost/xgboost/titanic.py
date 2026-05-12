import xgboost as xgb
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
import numpy as np


# Load Titanic dataset
titanic = sns.load_dataset('titanic')

# Print dataset info
print("\nDataset Info:")
print(titanic.info())

# Define the features list
features = ['pclass', 'sex', 'age', 'sibsp', 'parch', 'fare', 'embarked']

# Print missing values for the selected features
print("\nMissing Values Before Processing:")
print(titanic[features].isnull().sum())



# Select features and target
features = ['pclass', 'sex', 'age', 'sibsp', 'parch', 'fare', 'embarked']
X = titanic[features].copy()
y = titanic['survived']
print(f"\nTarget Value Counts:\n{y.value_counts()}")

# Handle missing values
X.loc[:, 'age'] = X['age'].fillna(X['age'].median())
X.loc[:, 'embarked'] = X['embarked'].fillna(X['embarked'].mode()[0])
print("\nMissing Values After Processing:")
print(X.isnull().sum())

# Apply one-hot encoding to categorical columns
X = pd.get_dummies(X, columns=['sex', 'embarked'], drop_first=True)
print("\nFinal DataFrame dtypes after one-hot encoding:")
print(X.dtypes)
print("\nColumns after encoding:", list(X.columns))
print("\nSample of Processed Data (first 5 rows):")
print(X.head())

# Split data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"\nTraining set shape: {X_train.shape}, Test set shape: {X_test.shape}")
print(f"Training target distribution:\n{y_train.value_counts()}")
print(f"Test target distribution:\n{y_test.value_counts()}")

# Initialize XGBoost model
model = xgb.XGBClassifier(random_state=42, use_label_encoder=False, eval_metric='logloss')

# Perform 5-fold cross-validation
cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
print(f"\nCross-validation accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
print(f"Individual CV fold accuracies: {[f'{score:.4f}' for score in cv_scores]}")

# Train the model
model.fit(X_train, y_train)

# Make predictions and probabilities
y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]
print("\nSample Predictions (first 5):")
print(f"True Labels: {y_test.values[:5]}")
print(f"Predicted Labels: {y_pred[:5]}")
print(f"Predicted Probabilities: {[f'{prob:.4f}' for prob in y_pred_proba[:5]]}")

# Evaluate accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"\nTest accuracy: {accuracy:.4f}")

# Feature Importance
importance = model.feature_importances_
feature_names = X.columns
feature_importance_df = pd.DataFrame({'Feature': feature_names, 'Importance': importance})
feature_importance_df = feature_importance_df.sort_values(by='Importance', ascending=False)
print("\nFeature Importance:")
print(feature_importance_df)
plt.figure(figsize=(10, 6))
plt.barh(feature_importance_df['Feature'], feature_importance_df['Importance'])
plt.xlabel('Feature Importance')
plt.ylabel('Features')
plt.title('Feature Importance in XGBoost Model')
plt.tight_layout()
plt.show()

# Evaluation Metrics
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
print(f"\nEvaluation Metrics:")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1 Score: {f1:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
print("\nConfusion Matrix (raw numbers):")
print(cm)
plt.figure(figsize=(6, 4))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.tight_layout()
plt.show()

