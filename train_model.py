import pandas as pd
import pickle
import os
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer

# Load your dataset (make sure 'dataset.csv' exists and has 'symptoms' & 'disease' columns)
data = pd.read_csv("symptom_drug_dataset_with_dosage.csv")

# Convert text symptoms into numerical features using TF-IDF
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(data["symptoms"])

# Convert disease labels into numerical classes
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(data["disease"])

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the XGBoost model
disease_model = xgb.XGBClassifier(use_label_encoder=False, eval_metric="mlogloss")
disease_model.fit(X_train, y_train)

# Create a directory to store the model
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

# Save the trained models
pickle.dump(disease_model, open(os.path.join(MODEL_DIR, "xgboost_model.pkl"), "wb"))
pickle.dump(vectorizer, open(os.path.join(MODEL_DIR, "vectorizer.pkl"), "wb"))
pickle.dump(label_encoder, open(os.path.join(MODEL_DIR, "label_encoder.pkl"), "wb"))

print("✅ Model, Vectorizer, and Label Encoder saved successfully!")

