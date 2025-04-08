import librosa
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
import joblib
# Load lại mô hình đã train
model = load_model("emotion_cnn1d_model.h5")

happy_file = "AudioWAV/1001_DFA_HAP_XX.wav"
neutral_file = "AudioWAV/1001_ITH_NEU_XX.wav"

# def extract_mfcc(filename):
#     y, sr = librosa.load(filename, duration=3, offset=0.5)
#     mfcc = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40).T, axis=0)
#     return mfcc

def extract_feature(filename):
    data,sampling_rate=librosa.load(filename,sr=16000)
    print(sampling_rate)
    result = np.array([])
    mfcc = np.mean(librosa.feature.mfcc(y=data, sr=sampling_rate, n_mfcc=40).T, axis=0)
    result = np.hstack((result, mfcc))

    result = np.array([])
    zcr = np.mean(librosa.feature.zero_crossing_rate(y=data).T, axis=0)
    result=np.hstack((result, zcr)) # stacking horizontally

    stft = np.abs(librosa.stft(data))
    chroma_stft = np.mean(librosa.feature.chroma_stft(S=stft, sr=sampling_rate).T, axis=0)
    result = np.hstack((result, chroma_stft)) # stacking horizontally

    # Root Mean Square Value --> ok
    rms = np.mean(librosa.feature.rms(y=data).T, axis=0)
    result = np.hstack((result, rms)) # stacking horizontally

        # MelSpectogram
    mel = np.mean(librosa.feature.melspectrogram(y=data, sr=sampling_rate).T, axis=0)
    result = np.hstack((result, mel)) # stacking horizontally

    return result

# hap_waveform = extract_mfcc(happy_file).reshape(1,-1)  # Thêm batch dimension và channel
# neu_waveform = extract_mfcc(neutral_file).reshape(1,-1)  # Thêm batch dimension và channel



# scaler=joblib.load('scaler.pkl')
# hap_waveform = scaler.transform(hap_waveform).reshape(1, 40, 1)
# neu_waveform = scaler.transform(neu_waveform).reshape(1, 40, 1)

hap_waveform1 = extract_feature(happy_file).reshape(1,-1)  # Thêm batch dimension và channel
neu_waveform1 = extract_feature(neutral_file).reshape(1,-1)  # Thêm batch dimension và channel



scaler=joblib.load('scaler.pkl')
hap_waveform1 = scaler.transform(hap_waveform1).reshape(1, 142, 1)
neu_waveform1 = scaler.transform(neu_waveform1).reshape(1, 142, 1)

# Dự đoán kết quả
hap_pred = model.predict(hap_waveform1)
neu_pred = model.predict(neu_waveform1)

# Chuyển output softmax thành nhãn
labels = ["Happy", "Neutral"]
hap_label = labels[np.argmax(hap_pred)]
neu_label = labels[np.argmax(neu_pred)]


print(f"Kết quả dự đoán cho file HAP: {hap_label}")
print(f"Kết quả dự đoán cho file NEU: {neu_label}")