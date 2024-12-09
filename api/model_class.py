import joblib
import numpy as np

class SentimentModel:
    def __init__(self):
        # Load the trained model and encoder
        self.model = joblib.load(r"C:\Users\m.pongsapat\OneDrive - Mitr Phol Sugar Corp., Ltd\Desktop\cedt\intro_to_datasci\Ds-DE-Project\encoder.pkl")
        self.encoder = joblib.load(r"C:\Users\m.pongsapat\OneDrive - Mitr Phol Sugar Corp., Ltd\Desktop\cedt\intro_to_datasci\Ds-DE-Project\sentiment_model.pkl")

    def predict_sentiment(self, keyword: str, year_range: str) -> int:
        # Prepare input data for prediction
        input_data = np.array([[keyword.lower(), year_range]])
        input_encoded = self.encoder.transform(input_data)

        # Predict sentiment
        sentiment = self.model.predict(input_encoded)[0]
        return int(sentiment)
