import os
import pandas as pd
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from imblearn.over_sampling import SMOTE

# Paths configuration
BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, 'risk_model.joblib')
ENC_SENDER_PATH = os.path.join(BASE_DIR, 'encoder_sender.joblib')
ENC_RECIPIENT_PATH = os.path.join(BASE_DIR, 'encoder_recipient.joblib')
ENC_RISK_PATH = os.path.join(BASE_DIR, 'encoder_risk.joblib')
DATA_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'transactions.csv'))

def load_data():
    """
    Load transaction data from CSV.
    """
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at: {DATA_PATH}")
    return pd.read_csv(DATA_PATH)

def main():
    # Load and prepare data
    df = load_data()
    enc_sender = LabelEncoder()
    enc_recipient = LabelEncoder()
    enc_risk = LabelEncoder()

    df['sender_enc'] = enc_sender.fit_transform(df['sender'])
    df['recipient_enc'] = enc_recipient.fit_transform(df['recipient'])
    df['risk_enc'] = enc_risk.fit_transform(df['risk'])

    X = df[['sender_enc', 'recipient_enc', 'amount_eth']]
    y = df['risk_enc']

    # Balance classes using SMOTE
    smote = SMOTE(k_neighbors=3, random_state=42)
    X_res, y_res = smote.fit_resample(X, y)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_res, y_res, test_size=0.2, random_state=42
    )

    # Hyperparameter grid for RandomForest
    param_grid = {
        'n_estimators': [100, 200],
        'max_depth': [None, 10, 20],
        'min_samples_split': [2, 5],
        'min_samples_leaf': [1, 2]
    }

    # Initialize and run GridSearch
    rf = RandomForestClassifier(random_state=42)
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        cv=3,
        n_jobs=-1,
        verbose=1
    )
    grid_search.fit(X_train, y_train)

    # Best model evaluation
    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test)
    print("[RESULT] Classification report:\n")
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=enc_risk.inverse_transform(sorted(y.unique()))
        )
    )

    # Save model and encoders
    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(enc_sender, ENC_SENDER_PATH)
    joblib.dump(enc_recipient, ENC_RECIPIENT_PATH)
    joblib.dump(enc_risk, ENC_RISK_PATH)
    print("[OK] Model and encoders saved to backend/ directory.")

if __name__ == '__main__':
    main()
