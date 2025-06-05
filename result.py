import socket
import numpy as np
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
HOST = '192.168.137.36'
PORT = 8888

# Cấu hình âm thanh
SAMPLE_RATE = 16000
SAMPLE_WIDTH = 4
CHANNELS = 1
PREDICT_INTERVAL = 2

class AudioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Realtime Audio Emotion Classifier")
        self.root.geometry("700x550")
        self.root.configure(bg="#f5f6fa")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 12), padding=8, background="#2980b9", foreground="#fff")
        style.configure("TLabel", font=("Segoe UI", 12), background="#f5f6fa")
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), background="#f5f6fa", foreground="#273c75")
        style.map("TButton", background=[("active", "#3498db")])

        self.is_recording = False
        self.audio_samples_list = []

        self.title_frame = tk.Frame(root, bg="#dff9fb", bd=2, relief="groove")
        self.title_frame.pack(pady=15, padx=15, fill=tk.X)
        self.label = ttk.Label(self.title_frame, text="ESP32 Audio & Emotion Prediction", style="Title.TLabel")
        self.label.pack(pady=8)

        self.canvas_frame = tk.Frame(root, bg="#f5f6fa", bd=2, relief="ridge")
        self.canvas_frame.pack(pady=10, padx=15, fill=tk.BOTH, expand=True)
        self.canvas = plt.Figure(figsize=(5, 3), dpi=100)
        self.ax = self.canvas.add_subplot(111)
        self.graph = FigureCanvasTkAgg(self.canvas, master=self.canvas_frame)
        self.graph.get_tk_widget().pack(pady=10, fill=tk.BOTH, expand=True)

        self.button_frame = tk.Frame(root, bg="#f5f6fa")
        self.button_frame.pack(pady=10)
        self.record_button = ttk.Button(self.button_frame, text="🎤 Start Recording", command=self.start_recording)
        self.record_button.grid(row=0, column=0, padx=10)
        self.stop_button = ttk.Button(self.button_frame, text="⏹ Stop Recording", command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=10)

        self.result_frame = tk.Frame(root, bg="#f5f6fa")
        self.result_frame.pack(pady=15)
        self.result_label = ttk.Label(self.result_frame, text="Emotion: None", font=("Segoe UI", 16, "bold"), background="#f5f6fa", foreground="#e17055")
        self.result_label.pack(pady=10)
        # Thêm vào phần __init__ sau dòng self.result_label.pack(pady=10)
        self.detail_label = ttk.Label(self.result_frame, text="", font=("Segoe UI", 12), background="#f5f6fa", foreground="#636e72")
        self.detail_label.pack(pady=5)

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
        try:
            self.client_socket.close()
        except Exception:
            pass
        self.record_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def update_waveform(self):
        self.ax.clear()
        self.ax.set_title("Waveform", fontsize=12, color="#273c75")
        ydata = np.array(self.audio_samples_list[-512:])
        xdata = np.arange(len(ydata))
        self.ax.plot(xdata, ydata, color='#0984e3')
        self.ax.set_facecolor("#f5f6fa")
        self.canvas.tight_layout()
        self.graph.draw()

    def extract_features(self, audio_data):
        data = np.array(audio_data, dtype=np.float32)
        
        # MFCC - tạo mảng result mới
        result = np.array([])
        mfcc = np.mean(librosa.feature.mfcc(y=data, sr=SAMPLE_RATE, n_mfcc=40).T, axis=0)
        result = np.hstack((result, mfcc))
        
        # Khởi tạo lại result giống với code huấn luyện
        result = np.array([])
        
        # Zero Crossing Rate
        zcr = np.mean(librosa.feature.zero_crossing_rate(y=data).T, axis=0)
        result = np.hstack((result, zcr))
        
        # Chroma STFT
        stft = np.abs(librosa.stft(data))
        chroma_stft = np.mean(librosa.feature.chroma_stft(S=stft, sr=SAMPLE_RATE).T, axis=0)
        result = np.hstack((result, chroma_stft))
        
        # RMS
        rms = np.mean(librosa.feature.rms(y=data).T, axis=0)
        result = np.hstack((result, rms))
        
        # Mel Spectrogram
        mel = np.mean(librosa.feature.melspectrogram(y=data, sr=SAMPLE_RATE).T, axis=0)
        result = np.hstack((result, mel))
        
        return result

    def predict_emotion(self):
        if not self.audio_samples_list:
            return
        try:
            features = self.extract_features(self.audio_samples_list).reshape(1, -1)
            print(f"Feature shape: {features.shape}")
            
            features = scaler.transform(features).reshape(1, 142, 1)
            prediction = model.predict(features)[0]
            labels = ["Happy", "Neutral"]
            
            # In ra xác suất và nhãn
            happy_prob = prediction[0] * 100
            neutral_prob = prediction[1] * 100
            
            emotion = labels[np.argmax(prediction)]
            confidence = np.max(prediction) * 100
            
            # Hiển thị emotion chính
            self.result_label.config(text=f"Emotion: {emotion} ({confidence:.1f}%)")
            
            # Hiển thị chi tiết probability cho cả hai cảm xúc
            self.detail_label.config(text=f"Happy: {happy_prob:.1f}% | Neutral: {neutral_prob:.1f}%")
            
        except Exception as e:
            print(f"Error in prediction: {str(e)}")
            self.result_label.config(text="Emotion: Error")
            self.detail_label.config(text="")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioApp(root)
    root.mainloop()