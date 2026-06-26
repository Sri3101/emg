from flask import Flask, render_template, jsonify, request
import joblib
import numpy as np
import pandas as pd
import sqlite3
import serial
import threading
import time
from datetime import datetime

app = Flask(__name__)

# Load model
model  = joblib.load('models/emg_model.pkl')
scaler = joblib.load('models/emg_scaler.pkl')

label_map = {0: 'Normal', 1: 'Moderate Fatigue', 2: 'High Fatigue'}

# Global serial state
serial_port   = None
session_data  = {
    'running':   False,
    'buffer':    [],
    'result':    None,
    'progress':  0,
    'latest_rms': 0
}
SESSION_SIZE = 20

# ── Database ────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect('database/sessions.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            patient     TEXT,
            avg_rms     REAL,
            label       TEXT,
            confidence  REAL,
            timestamp   TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_session(patient, avg_rms, label, confidence):
    conn = sqlite3.connect('database/sessions.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO sessions (patient, avg_rms, label, confidence, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (patient, avg_rms, label, confidence, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def get_all_sessions():
    conn = sqlite3.connect('database/sessions.db')
    c = conn.cursor()
    c.execute('SELECT * FROM sessions ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    return rows

# ── Serial Reader ────────────────────────────────────────────
def read_serial(patient_name):
    global serial_port, session_data
    session_data['running']  = True
    session_data['buffer']   = []
    session_data['result']   = None
    session_data['progress'] = 0

    try:
        serial_port = serial.Serial('COM5', 115200, timeout=1)
        time.sleep(2)

        while session_data['running']:
            line = serial_port.readline().decode('utf-8').strip()
            if line:
                try:
                    rms = float(line)
                    session_data['latest_rms'] = round(rms, 1)
                    session_data['buffer'].append(rms)
                    session_data['progress'] = len(session_data['buffer'])

                    if len(session_data['buffer']) >= SESSION_SIZE:
                        avg_rms    = np.mean(session_data['buffer'])
                        scaled     = scaler.transform(pd.DataFrame([[avg_rms]], columns=['rms']))
                        pred       = model.predict(scaled)[0]
                        prob       = model.predict_proba(scaled)[0]
                        confidence = round(float(max(prob)) * 100, 1)
                        label      = label_map[pred]

                        session_data['result'] = {
                            'avg_rms':    round(avg_rms, 1),
                            'label':      label,
                            'confidence': confidence,
                            'patient':    patient_name
                        }
                        save_session(patient_name, avg_rms, label, confidence)
                        session_data['running'] = False

                except ValueError:
                    pass

    except Exception as e:
        session_data['result'] = {'error': str(e)}
        session_data['running'] = False
    finally:
        if serial_port and serial_port.is_open:
            serial_port.close()

# ── Routes ───────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return render_template('test.html')

@app.route('/history')
def history():
    rows = get_all_sessions()
    sessions = [{
        'id':         r[0],
        'patient':    r[1],
        'avg_rms':    r[2],
        'label':      r[3],
        'confidence': r[4],
        'timestamp':  r[5]
    } for r in rows]
    return render_template('history.html', sessions=sessions)

@app.route('/api/start', methods=['POST'])
def start_session():
    data         = request.json
    patient_name = data.get('patient', 'Unknown')
    t = threading.Thread(target=read_serial, args=(patient_name,))
    t.daemon = True
    t.start()
    return jsonify({'status': 'started'})

@app.route('/api/status')
def status():
    return jsonify({
        'running':    session_data['running'],
        'progress':   session_data['progress'],
        'total':      SESSION_SIZE,
        'latest_rms': session_data['latest_rms'],
        'result':     session_data['result']
    })

@app.route('/api/history')
def api_history():
    rows = get_all_sessions()
    return jsonify([{
        'id':         r[0],
        'patient':    r[1],
        'avg_rms':    r[2],
        'label':      r[3],
        'confidence': r[4],
        'timestamp':  r[5]
    } for r in rows])

@app.route('/api/delete/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    conn = sqlite3.connect('database/sessions.db')
    c = conn.cursor()
    c.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted', 'id': session_id})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)