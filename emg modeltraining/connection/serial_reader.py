import serial
import joblib
import pandas as pd
import numpy as np

model  = joblib.load(r'C:\Users\sAadh\Downloads\emg project\emg_model.pkl')
scaler = joblib.load(r'C:\Users\sAadh\Downloads\emg project\emg_scaler.pkl')

label_map = {0: '✅ Normal', 1: '⚠️ Moderate Fatigue', 2: '🔴 High Fatigue'}

ser = serial.Serial('COM5', 115200, timeout=1)
print("Connected. Starting session...\n")

SESSION_SIZE = 20  # collect 20 readings then predict once
buffer = []

while True:
    line = ser.readline().decode('utf-8').strip()
    if line:
        try:
            rms = float(line)
            buffer.append(rms)
            print(f"  Reading {len(buffer)}/{SESSION_SIZE}: RMS = {rms:.1f}", end='\r')

            if len(buffer) >= SESSION_SIZE:
                avg_rms = np.mean(buffer)
                scaled  = scaler.transform(pd.DataFrame([[avg_rms]], columns=['rms']))
                pred    = model.predict(scaled)[0]
                prob    = model.predict_proba(scaled)[0]

                print(f"\n{'='*50}")
                print(f"Average RMS : {avg_rms:.1f}")
                print(f"Result      : {label_map[pred]}")
                print(f"Confidence  : {max(prob)*100:.1f}%")
                print(f"{'='*50}\n")

                buffer = []  # reset for next session

        except ValueError:
            pass