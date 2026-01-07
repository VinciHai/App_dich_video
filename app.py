import streamlit as st  # Thư viện tạo giao diện Web
import os               # Thư viện quản lý file trong hệ điều hành
import moviepy.editor as mp # Thư viện xử lý video và cắt âm thanh
import speech_recognition as sr # Thư viện chuyển đổi giọng nói thành văn bản
import google.generativeai as genai # Thư viện kết nối với AI Gemini

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="Công cụ Dịch Phụ Đề AI", page_icon="🎬")
st.title("🎬 Ứng dụng Tạo Phụ đề Video bằng AI")
st.write("Tải video lên -> Tách âm thanh -> Chuyển thành chữ -> Dịch sang tiếng Việt.")

# --- BƯỚC 1: NHẬP API KEY ---
# Tạo một ô bên thanh menu trái để bạn nhập khóa bí mật (API Key)
api_key = st.sidebar.text_input("Nhập Google Gemini API Key của bạn:", type="password")

# --- HÀM XỬ LÝ CHÍNH (LOGIC) ---
def process_video(uploaded_file, api_key):
    # Cấu hình AI Gemini với key bạn vừa nhập
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro') # Sử dụng mô hình Gemini Pro

    status_text = st.empty() # Tạo một chỗ trống để hiện thông báo trạng thái
    progress_bar = st.progress(0) # Thanh tiến trình

    try:
        # 1. LƯU FILE VIDEO TẠM THỜI
        status_text.text("⏳ Đang lưu video...")
        with open("temp_video.mp4", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 2. TRÍCH XUẤT ÂM THANH (MoviePy)
        status_text.text("⏳ Đang tách âm thanh từ video...")
        progress_bar.progress(20)
        video_clip = mp.VideoFileClip("temp_video.mp4")
        # Chuyển thành file wav để thư viện SpeechRecognition dễ đọc
        video_clip.audio.write_audiofile("temp_audio.wav", codec='pcm_s16le') 
        
        # 3. CHUYỂN ÂM THANH THÀNH CHỮ (SpeechRecognition)
        status_text.text("⏳ Đang nghe và chép lại tiếng Anh...")
        progress_bar.progress(40)
        recognizer = sr.Recognizer()
        with sr.AudioFile("temp_audio.wav") as source:
            audio_data = recognizer.record(source)
            # Dùng Google Speech để nhận diện tiếng Anh (en-US)
            english_text = recognizer.recognize_google(audio_data, language="en-US")
        
        # 4. DỊCH THUẬT BẰNG GEMINI
        status_text.text("⏳ Đang gửi cho Gemini dịch sang tiếng Việt...")
        progress_bar.progress(70)
        
        # Viết câu lệnh (Prompt) cho AI
        prompt = f"""
        Bạn là một chuyên gia dịch thuật phim ảnh. Hãy dịch đoạn văn bản tiếng Anh sau đây sang tiếng Việt.
        Yêu cầu: Dịch tự nhiên, văn phong đời thường, phù hợp làm phụ đề phim.
        
        Văn bản gốc: "{english_text}"
        """
        response = model.generate_content(prompt)
        vietnamese_text = response.text
        
        progress_bar.progress(100)
        status_text.text("✅ Hoàn tất!")

        # 5. DỌN DẸP FILE RÁC
        video_clip.close() # Đóng file video
        os.remove("temp_video.mp4") # Xóa video tạm
        os.remove("temp_audio.wav") # Xóa audio tạm

        return english_text, vietnamese_text

    except Exception as e:
        status_text.text("❌ Có lỗi xảy ra!")
        st.error(f"Lỗi chi tiết: {e}")
        return None, None

# --- GIAO DIỆN CHÍNH ---
uploaded_file = st.file_uploader("Chọn file video của bạn (MP4)", type=["mp4"])

if uploaded_file is not None:
    # Hiện video lên màn hình để xem trước
    st.video(uploaded_file)
    
    # Nút bấm bắt đầu
    if st.button("Bắt đầu xử lý"):
        if not api_key:
            st.warning("Vui lòng nhập API Key ở thanh bên trái trước!")
        else:
            # Gọi hàm xử lý ở trên
            en_sub, vn_sub = process_video(uploaded_file, api_key)
            
            if en_sub and vn_sub:
                # Chia màn hình làm 2 cột
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Tiếng Anh (Gốc)")
                    st.text_area("Original", en_sub, height=300)
                
                with col2:
                    st.subheader("Tiếng Việt (Dịch)")
                    st.text_area("Translated", vn_sub, height=300)
                
                # Tạo file txt để tải về
                st.download_button(
                    label="📥 Tải phụ đề Tiếng Việt (.txt)",
                    data=vn_sub,
                    file_name="phude_viet.txt",
                    mime="text/plain"
                )