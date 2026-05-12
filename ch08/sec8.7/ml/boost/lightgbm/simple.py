import lightgbm as lgb
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from sklearn.datasets import fetch_openml

# Load Credit Approval dataset (real-world data)
print("Loading credit approval dataset ..")
credit_data = fetch_openml(name='credit-approval', version=1, as_frame=True)
X = credit_data.data
y = credit_data.target

print(f"Dataset shape: {X.shape}")
print(f"Target classes: {np.unique(y)}")

# Handle missing values and categorical variables
X = X.copy()
for col in X.columns:
    if X[col].dtype == 'object' or X[col].dtype.name == 'category':
        # Fill missing categorical values with mode
        X[col] = X[col].fillna(X[col].mode()[0])
        # Encode categorical variables
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
    else:
        # Convert to numeric and fill missing values with median
        X[col] = pd.to_numeric(X[col], errors='coerce')
        X[col] = X[col].fillna(X[col].median())

# Encode target variable
le_target = LabelEncoder()
y = le_target.fit_transform(y)

print(f"Processed data shape: {X.shape}")
print(f"Features: {list(X.columns)}")

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, 
                                                    random_state=42, stratify=y)

# Create LightGBM datasets
train_data = lgb.Dataset(X_train, label=y_train)
test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

# Set parameters for credit approval prediction
params = {
    'objective': 'binary',
    'metric': 'binary_logloss',
    'boosting_type': 'gbdt',
    'num_leaves': 20,
    'learning_rate': 0.1,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'min_data_in_leaf': 10,
    'lambda_l2': 0.1,
    'verbose': -1
}

# Train the model
print("\nTraining credit approval model ..")
model = lgb.train(params,
                  train_data,
                  valid_sets=[test_data],
                  num_boost_round=100,
                  callbacks=[lgb.early_stopping(stopping_rounds=10)])

print(f"Best iteration: {model.best_iteration}")
print(f"Best validation score: {model.best_score['valid_0']['binary_logloss']:.6f}")

# Make predictions
y_pred = model.predict(X_test, num_iteration=model.best_iteration)
y_pred_binary = (y_pred > 0.5).astype(int)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred_binary)
print(f"\nCredit Approval Model Performance:")
print(f"Accuracy: {accuracy:.4f}")

# Detailed classification report
target_names = ['Denied', 'Approved']
print("\nClassification Report:")
print(classification_report(y_test, y_pred_binary, target_names=target_names))

# Feature importance analysis
feature_importance = model.feature_importance()
feature_names = list(X.columns)

# Create feature importance dataframe
importance_df = pd.DataFrame({
    'feature': feature_names,
    'importance': feature_importance
}).sort_values('importance', ascending=False)

print("\nTop 10 Most Important Features for Credit Approval:")
print(importance_df.head(10).to_string(index=False))

# Prediction example
print("\nExample prediction:")
sample_idx = 0
sample_features = X_test.iloc[sample_idx:sample_idx+1]
sample_pred = model.predict(sample_features, num_iteration=model.best_iteration)[0]
actual_result = 'Approved' if y_test[sample_idx] == 1 else 'Denied'
predicted_result = 'Approved' if sample_pred > 0.5 else 'Denied'

print(f"Actual: {actual_result}")
print(f"Predicted: {predicted_result} (confidence: {sample_pred:.3f})")

