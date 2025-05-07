import pickle
import numpy as np
import xgboost as xgb

# Load the trained model
with open("xgboost_model.pkl", "rb") as model_file:
    model = pickle.load(model_file)

# Load the label encoder
with open("label_encoder.pkl", "rb") as encoder_file:
    label_encoder = pickle.load(encoder_file)

# Function to make predictions
def predict_drug(symptoms):
    try:
        # Convert symptoms to numerical format (Assumes pre-processing is done)
        symptom_codes = np.array(symptoms).reshape(1, -1)

        # Make a prediction
        prediction = model.predict(symptom_codes)

        # Convert prediction back to drug name
        predicted_drug = label_encoder.inverse_transform(prediction)[0]

        return f"Recommended Drug: {predicted_drug}"
    
    except Exception as e:
        return f"Error: {str(e)}"

# Example usage
if __name__ == "__main__":
    # Example symptom input (replace with actual symptom codes)
    sample_input = [1, 2, 5, 0, 3, 7, 8, 0]  # Replace with real values
    result = predict_drug(sample_input)
    print(result)

