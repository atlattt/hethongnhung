import socket
import wave
import numpy as np
import time
import matplotlib.pyplot as plt # Thêm thư viện matplotlib

# import pyaudio  # Thư viện để phát âm thanh (tùy chọn)
    
# Thông tin kết nối đến ESP32 (thay đổi địa chỉ IP nếu cần)
HOST = '192.168.137.23' # Điền địa chỉ IP của ESP32 mà bạn thấy trên Serial Monitor
PORT = 8888

# Cấu hình âm thanh (phải khớp với cấu hình I2S trên ESP32)
SAMPLE_RATE = 16000
SAMPLE_WIDTH = 4  # 4 bytes cho 32-bit int (int32_t)
CHANNELS = 1

def save_wav(filename, data):
    """Lưu dữ liệu âm thanh numpy array thành file WAV."""
    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(SAMPLE_WIDTH)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(data.tobytes()) # Chuyển numpy array về bytes và ghi
    wf.close()
    print(f"Đã lưu file WAV: {filename}")


# def play_audio_pyaudio(data): # Hàm phát âm thanh dùng PyAudio (tùy chọn)
#     p = pyaudio.PyAudio()
#     stream = p.open(format=pyaudio.paInt32, # Phải khớp với SAMPLE_WIDTH
#                     channels=CHANNELS,
#                     rate=SAMPLE_RATE,
#                     output=True)
#     stream.write(data.tobytes()) # Phát dữ liệu
#     stream.stop_stream()
#     stream.close()
#     p.terminate()


# def receive_audio_stream():
#     """Nhận stream âm thanh từ ESP32 qua TCP và xử lý."""
#     client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#
#     try:
#         client_socket.connect((HOST, PORT))
#         print(f"Đã kết nối đến ESP32: {HOST}:{PORT}")
#
#         audio_data_bytes = b'' # Khởi tạo bytes rỗng để tích lũy dữ liệu
#         total_received_samples = 0
#         recording_duration_sec = 10 # Ví dụ: ghi 10 giây
#         expected_samples = SAMPLE_RATE * recording_duration_sec # Số mẫu dự kiến
#
#         print(f"Bắt đầu nhận stream âm thanh trong {recording_duration_sec} giây...")
#         while total_received_samples < expected_samples: # Nhận cho đến khi đủ mẫu hoặc ngắt kết nối
#             chunk = client_socket.recv(4096) # Nhận tối đa 4096 bytes mỗi lần
#             if not chunk: # Nếu không nhận được dữ liệu nữa (ngắt kết nối)
#                 print("ESP32 ngắt kết nối.")
#                 break
#             audio_data_bytes += chunk
#             received_samples_in_chunk = len(chunk) // SAMPLE_WIDTH # Số mẫu nhận được trong chunk
#             total_received_samples += received_samples_in_chunk
#             print(f"Đã nhận {received_samples_in_chunk} mẫu, tổng cộng {total_received_samples}/{expected_samples} mẫu.")
#
#
#         print("Hoàn thành nhận stream.")
#
#         # Chuyển bytes nhận được thành numpy array (int32)
#         audio_data_np = np.frombuffer(audio_data_bytes, dtype=np.int32)
#         print(f"Dữ liệu âm thanh nhận được: {len(audio_data_bytes)} bytes, {len(audio_data_np)} samples")
#
#
#         # Lưu thành file WAV (tùy chọn)
#         filename = f"{int(time.time())}.wav"
#         save_wav(filename, audio_data_np)
#
#         # Phát âm thanh trực tiếp dùng PyAudio (tùy chọn - cần cài pyaudio)
#         # play_audio_pyaudio(audio_data_np)
#
#
#     except socket.error as e:
#         print(f"Lỗi socket: {e}")
#     finally:
#         client_socket.close()
def receive_audio_stream(): # Đổi tên hàm để rõ ràng hơn
    """Nhận stream âm thanh từ ESP32 qua TCP và vẽ đồ thị dạng sóng."""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((HOST, PORT))
        print(f"Đã kết nối đến ESP32: {HOST}:{PORT}")

        audio_data_bytes = b'' # Bytes rỗng ban đầu
        audio_samples_list = [] # Danh sách để lưu trữ các mẫu âm thanh (numpy array)
        total_received_samples = 0
        recording_duration_sec = 10 # Ví dụ: ghi 10 giây
        expected_samples = SAMPLE_RATE * recording_duration_sec

        plt.ion() # Bật chế độ interactive để đồ thị cập nhật liên tục (tùy chọn)
        fig, ax = plt.subplots() # Tạo figure và axes cho đồ thị
        line, = ax.plot([], []) # Tạo line object để cập nhật dữ liệu đồ thị
        ax.set_xlim(0, 512) # Giới hạn trục x (ví dụ: hiển thị 512 mẫu mỗi lần)
        ax.set_ylim(-30000000, 30000000) # Giới hạn trục y (tùy theo dải giá trị mẫu 32-bit)
        ax.set_title("Dạng Sóng Âm Thanh Theo Thời Gian Thực")
        ax.set_xlabel("Mẫu")
        ax.set_ylabel("Giá trị Mẫu")
        ax.grid(True)


        print(f"Bắt đầu nhận stream và vẽ đồ thị trong {recording_duration_sec} giây...")
        while total_received_samples < expected_samples:
            chunk = client_socket.recv(4096)
            if not chunk:
                print("ESP32 ngắt kết nối.")
                break
            audio_data_bytes += chunk
            received_samples_in_chunk = len(chunk) // SAMPLE_WIDTH
            total_received_samples += received_samples_in_chunk
            print(f"Đã nhận {received_samples_in_chunk} mẫu, tổng cộng {total_received_samples}/{expected_samples} mẫu.")

            # Chuyển chunk bytes thành numpy array
            audio_chunk_np = np.frombuffer(chunk, dtype=np.int32)
            audio_samples_list.extend(audio_chunk_np) # Thêm vào danh sách mẫu

            # Vẽ đồ thị (cập nhật dữ liệu) - vẽ mỗi chunk nhận được
            ydata = np.array(audio_samples_list[-512:]) # Lấy 512 mẫu cuối để vẽ (ví dụ)
            xdata = np.arange(len(ydata)) # Tạo trục x tương ứng
            line.set_data(xdata, ydata) # Cập nhật dữ liệu cho line object
            ax.relim() # Cập nhật lại giới hạn trục y dựa trên dữ liệu mới
            ax.autoscale_view(True,True,True) # Tự động điều chỉnh scale trục y
            fig.canvas.draw() # Vẽ lại figure
            fig.canvas.flush_events() # Xử lý sự kiện vẽ


        print("Hoàn thành nhận stream và vẽ đồ thị.")

        audio_data_np = np.array(audio_samples_list) # Chuyển danh sách mẫu thành numpy array cuối cùng
        print(f"Dữ liệu âm thanh nhận được: {len(audio_data_bytes)} bytes, {len(audio_data_np)} samples")


        # Lưu thành file WAV (tùy chọn)
        filename = f"{int(time.time())}.wav"
        save_wav(filename, audio_data_np)

        # Phát âm thanh trực tiếp dùng PyAudio (tùy chọn)
        # play_audio_pyaudio(audio_data_np)


    except socket.error as e:
        print(f"Lỗi socket: {e}")
    finally:
        client_socket.close()
        plt.ioff() # Tắt chế độ interactive khi kết thúc
        # plt.show() # Hiển thị đồ thị cuối cùng (nếu chế độ interactive tắt)

    return 0

if __name__ == "__main__":
    while(1):
        receive_audio_stream()
