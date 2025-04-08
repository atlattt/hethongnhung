import os
import socket
import wave
import numpy as np
import time
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import librosa
import tensorflow as tf
from tensorflow.keras.models import load_model
import joblib

# Load model và scaler
MODEL_PATH = "emotion_cnn1d_model.h5"
SCALER_PATH = "scaler.pkl"
model = load_model(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

# Thông tin kết nối đến ESP32
HOST = '192.168.137.89'  # Địa chỉ IP của ESP32
PORT = 8888

# Cấu hình âm thanh
SAMPLE_RATE = 16000
SAMPLE_WIDTH = 4  
CHANNELS = 1
PREDICT_INTERVAL = 2  # Dự đoán mỗi 2 giây

class AudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Realtime Audio Emotion Classifier")
        self.root.geometry("600x500")
        
        self.is_recording = False
        self.audio_samples_list = []
        
        self.label = ttk.Label(root, text="ESP32 Audio & Emotion Prediction", font=("Helvetica", 16, "bold"))
        self.label.pack(pady=10)
        
        self.canvas = plt.Figure(figsize=(5, 3), dpi=100)
        self.ax = self.canvas.add_subplot(111)
        self.graph = FigureCanvasTkAgg(self.canvas, master=root)
        self.graph.get_tk_widget().pack(pady=10, fill=tk.BOTH, expand=True)

        self.record_button = ttk.Button(root, text="Start Recording", command=self.start_recording)
        self.record_button.pack(pady=5)
        
        self.stop_button = ttk.Button(root, text="Stop Recording", command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.pack(pady=5)
        
        self.result_label = ttk.Label(root, text="Emotion: None", font=("Helvetica", 14, "bold"))
        self.result_label.pack(pady=10)

    def start_recording(self):
        self.is_recording = True
        self.audio_samples_list = []
        self.record_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect((HOST, PORT))
            self.root.after(100, self.receive_audio_stream)
        except socket.error as e:
            messagebox.showerror("Error", f"Socket error: {e}")
            self.stop_recording()
    
    def receive_audio_stream(self):
        if not self.is_recording:
            return
        try:
            chunk = self.client_socket.recv(4096)
            if not chunk:
                self.stop_recording()
                return
            
            audio_chunk_np = np.frombuffer(chunk, dtype=np.int32)
            self.audio_samples_list.extend(audio_chunk_np)
            self.update_waveform()
            
            if len(self.audio_samples_list) >= SAMPLE_RATE * PREDICT_INTERVAL:
                self.predict_emotion()
                self.audio_samples_list = []
            
            self.root.after(100, self.receive_audio_stream)
        except socket.error as e:
            messagebox.showerror("Error", f"Socket error: {e}")
            self.stop_recording()
    
    def stop_recording(self):
        self.is_recording = False
        self.client_socket.close()
        self.record_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def update_waveform(self):
        self.ax.clear()
        self.ax.set_title("Waveform")
        ydata = np.array(self.audio_samples_list[-512:])
        xdata = np.arange(len(ydata))
        self.ax.plot(xdata, ydata, color='#3498db')
        self.graph.draw()

    def extract_features(self, audio_data):
        data = np.array(audio_data, dtype=np.float32)
        result = np.array([])
        mfcc = np.mean(librosa.feature.mfcc(y=data, sr=SAMPLE_RATE, n_mfcc=40).T, axis=0)
        result = np.hstack((result, mfcc))

        result = np.array([])
        zcr = np.mean(librosa.feature.zero_crossing_rate(y=data).T, axis=0)
        result=np.hstack((result, zcr)) # stacking horizontally

        stft = np.abs(librosa.stft(data))
        chroma_stft = np.mean(librosa.feature.chroma_stft(S=stft, sr=SAMPLE_RATE).T, axis=0)
        result = np.hstack((result, chroma_stft)) # stacking horizontally

        # Root Mean Square Value --> ok
        rms = np.mean(librosa.feature.rms(y=data).T, axis=0)
        result = np.hstack((result, rms)) # stacking horizontally

            # MelSpectogram
        mel = np.mean(librosa.feature.melspectrogram(y=data, sr=SAMPLE_RATE).T, axis=0)
        result = np.hstack((result, mel)) # stacking horizontally

        return result
        
    def predict_emotion(self):
        if not self.audio_samples_list:
            return
        features = self.extract_features(self.audio_samples_list).reshape(1, -1)
        features = scaler.transform(features).reshape(1, 142, 1)
        prediction = model.predict(features)
        labels = ["Happy", "Neutral"]
        emotion = labels[np.argmax(prediction)]
        self.result_label.config(text=f"Emotion: {emotion}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioApp(root)
    root.mainloop()
