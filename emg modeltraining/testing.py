import joblib
import numpy as np
import pandas as pd

model  = joblib.load('emg_model.pkl')
scaler = joblib.load('emg_scaler.pkl')

label_map = {0: 'Normal', 1: 'Moderate Fatigue', 2: 'High Fatigue'}

test_values = [2080, 2500, 2050]
for val in test_values:
    scaled = scaler.transform(pd.DataFrame([[val]], columns=['rms']))
    pred   = model.predict(scaled)[0]
    prob   = model.predict_proba(scaled)[0]
    print(f"RMS: {val} → {label_map[pred]} (Normal:{prob[0]*100:.1f}% | Moderate:{prob[1]*100:.1f}% | High:{prob[2]*100:.1f}%)")