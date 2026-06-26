import numpy as np
import pandas as pd

np.random.seed(42)
samples_per_class = 1000

def generate_class(center, spread, noise, n):
    # Base signal with realistic drift
    base = np.random.normal(center, spread, n)
    # Add slight temporal drift (fatigue builds gradually)
    drift = np.linspace(0, noise * 0.3, n)
    noise_arr = np.random.normal(0, noise, n)
    return np.clip(base + drift + noise_arr, 1800, 3200)

normal   = generate_class(center=1950, spread=60,  noise=40,  n=samples_per_class)
moderate = generate_class(center=2200, spread=80,  noise=70,  n=samples_per_class)
high     = generate_class(center=2800, spread=100, noise=120, n=samples_per_class)

rms_values = np.concatenate([normal, moderate, high])
labels     = np.array([0]*samples_per_class + [1]*samples_per_class + [2]*samples_per_class)

df = pd.DataFrame({'rms': rms_values, 'label': labels})
df = df.sample(frac=1).reset_index(drop=True)  # shuffle
df.to_csv('emg_data.csv', index=False)
print(df['label'].value_counts())
print(df.describe())