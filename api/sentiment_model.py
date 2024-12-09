import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

# Load the dataset
data = pd.read_csv(r"C:\Users\m.pongsapat\OneDrive - Mitr Phol Sugar Corp., Ltd\Desktop\cedt\intro_to_datasci\Ds-DE-Project\data\keyword_sentiment.csv")

# Prepare features (keyword and year_range) and target (sentiment)
X = data[["keyword", "year_range"]]
y = data["sentiment"]

# One-hot encode the categorical features
encoder = OneHotEncoder()
X_encoded = encoder.fit_transform(X)

# Split into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.2, random_state=42)

# Train a linear regression model
model = LinearRegression()
model.fit(X_train, y_train)

# Save the encoder and model for later use
import joblib
joblib.dump(encoder, "encoder.pkl")
joblib.dump(model, "sentiment_model.pkl")
