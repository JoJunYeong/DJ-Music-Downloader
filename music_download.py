import tkinter as tk
from tkinter import ttk, messagebox
from pydub import AudioSegment
import os
import threading
import yt_dlp

# URL 저장 및 로드에 사용할 파일 경로
URL_FILE = "urls.txt"

# "music" 폴더가 없으면 생성
def ensure_music_folder_exists():
    music_folder = "music"
    if not os.path.exists(music_folder):
        os.makedirs(music_folder)
    return music_folder

# 로그 메시지 출력 함수
def log_message(log_widget, message):
    log_widget.insert(tk.END, message + "\n")
    log_widget.see(tk.END)

# yt-dlp 로그를 tkinter 로그 창에 출력하는 함수
def yt_dlp_hook(d, log_widget):
    if d['status'] == 'downloading':
        log_message(log_widget, f"[download] {d['_percent_str']} of {d['_total_bytes_str']} at {d['_speed_str']} ETA {d['_eta_str']}")
    elif d['status'] == 'finished':
        log_message(log_widget, "다운로드 완료, 파일 처리 중...")

# 재생목록 또는 단일 영상 다운로드
def download_video_or_playlist(url, log_widget):
    try:
        log_message(log_widget, f"다운로드 시작: {url}")
        music_folder = ensure_music_folder_exists()  # music 폴더 생성 및 경로 확인
        ydl_opts = {
            'format': 'bestaudio',
            'outtmpl': 'music/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks': [lambda d: yt_dlp_hook(d, log_widget)]
        }

        # yt-dlp를 통해 재생목록 또는 단일 영상 다운로드
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)  # 정보를 가져오고 다운로드
            if 'entries' in info_dict:  # 재생목록인 경우
                for entry in info_dict['entries']:
                    title = entry.get('title', 'Unknown')
                    log_message(log_widget, f"재생목록에서 다운로드 완료: {title}")
                    mp3_file_path = os.path.join(music_folder, f"{title}.mp3")
                    normalize_audio(mp3_file_path, log_widget)
            else:  # 단일 영상인 경우
                title = info_dict.get('title', 'Unknown')
                mp3_file_path = os.path.join(music_folder, f"{title}.mp3")
                normalize_audio(mp3_file_path, log_widget)
    except Exception as e:
        log_message(log_widget, f"다운로드 중 오류 발생: {str(e)}")

# 오디오 파일의 볼륨 조정 및 덮어쓰기
def normalize_audio(file_path, log_widget, target_dBFS=-10.0):
    try:
        log_message(log_widget, f"볼륨 조정 중: {file_path}")
        sound = AudioSegment.from_file(file_path, format="mp3")
        change_in_dBFS = target_dBFS - sound.dBFS
        normalized_sound = sound.apply_gain(change_in_dBFS)

        # 기존 파일 덮어쓰기
        normalized_sound.export(file_path, format="mp3")
        log_message(log_widget, f"볼륨 조정 완료 및 파일 덮어쓰기 완료: {file_path}")
    except Exception as e:
        log_message(log_widget, f"볼륨 조정 오류: {file_path} - {str(e)}")

# URL 리스트를 처리하는 함수
def process_urls(urls, log_widget, progress_bar, progress_label):
    total_urls = len(urls)
    completed = 0

    for url in urls:
        try:
            download_video_or_playlist(url, log_widget)  # yt-dlp를 사용하여 다운로드
            completed += 1
            percentage = (completed / total_urls) * 100
            progress_bar['value'] = percentage  # 프로그레스바 업데이트
            progress_label.config(text=f"{completed}/{total_urls} 완료 ({int(percentage)}%)")  # 완료된 개수 및 퍼센트 업데이트
        except Exception as e:
            log_message(log_widget, f"처리 중 오류 발생: {str(e)}")

# URL 목록을 파일에 저장
def save_urls(urls):
    with open(URL_FILE, 'w') as f:
        for url in urls:
            f.write(f"{url}\n")

# URL 목록을 파일에서 로드
def load_urls():
    if os.path.exists(URL_FILE):
        with open(URL_FILE, 'r') as f:
            return f.read().splitlines()
    return []



# 텍스트 복사 기능 추가
def copy_text(event, log_widget):
    try:
        selected_text = log_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        log_widget.clipboard_clear()
        log_widget.clipboard_append(selected_text)
    except tk.TclError:
        pass  # 선택된 텍스트가 없을 경우 무시

# 쓰레딩을 사용하여 작업을 백그라운드에서 실행
def start_processing_thread(urls, log_widget, progress_bar, progress_label):
    thread = threading.Thread(target=process_urls, args=(urls, log_widget, progress_bar, progress_label))
    thread.start()
# URL 입력 및 처리 GUI
def start_gui():
    def on_process():
        urls = url_text.get("1.0", tk.END).strip().split("\n")
        save_urls(urls)  # URL을 저장
        if urls:
            total_urls = len(urls)
            progress_bar['value'] = 0  # 프로그레스바 초기화
            progress_label.config(text=f"0/{total_urls} 완료 (0%)")  # 총 개수 설정
            start_processing_thread(urls, log_text, progress_bar, progress_label)  # 프로세스 백그라운드에서 실행
        else:
            messagebox.showerror("오류", "URL이 입력되지 않았습니다.")

    # 기본 GUI 설정
    window = tk.Tk()
    window.title("YouTube 오디오 다운로드 및 볼륨 조정")

    # URL 입력을 위한 텍스트 박스
    tk.Label(window, text="YouTube URL 목록 (한 줄에 하나씩 입력)").pack()
    url_text = tk.Text(window, height=10, width=100)
    url_text.pack()

    # 이전에 저장된 URL 목록을 불러오기
    saved_urls = load_urls()
    if saved_urls:
        url_text.insert(tk.END, "\n".join(saved_urls))

    # 실행 버튼
    process_button = tk.Button(window, text="처리 시작", command=on_process)
    process_button.pack()

    # 로그 표시를 위한 텍스트 박스
    tk.Label(window, text="로그 창").pack()
    log_text = tk.Text(window, height=10, width=100)
    log_text.pack()

    # 프로그레스 바 및 진행 상태 라벨 추가
    progress_bar = ttk.Progressbar(window, mode="determinate")
    progress_bar.pack(pady=10)
    progress_label = tk.Label(window, text="0/0 완료 (0%)")
    progress_label.pack()

    # 텍스트 복사, 붙여넣기, 전체 선택 기능을 위한 키 바인딩 추가 (Mac용 Cmd 키)
    url_text.bind("<Command-a>", lambda event: select_all(event, url_text))  # macOS
    log_text.bind("<Command-a>", lambda event: select_all(event, log_text))  # macOS

    url_text.bind("<Command-c>", lambda event: copy_text(event, url_text))  # macOS
    log_text.bind("<Command-c>", lambda event: copy_text(event, log_text))  # macOS

    url_text.bind("<Command-v>", lambda event: paste_text(event, url_text))  # macOS
    log_text.bind("<Command-v>", lambda event: paste_text(event, log_text))  # macOS

    # GUI 실행
    window.mainloop()

# 텍스트 복사 기능 추가
def copy_text(event, widget):
    try:
        selected_text = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        widget.clipboard_clear()
        widget.clipboard_append(selected_text)
    except tk.TclError:
        pass  # 선택된 텍스트가 없을 경우 무시
    return 'break'

# 텍스트 붙여넣기 기능 추가
def paste_text(event, widget):
    try:
        clipboard_text = widget.clipboard_get()
        widget.insert(tk.INSERT, clipboard_text)
    except tk.TclError:
        pass  # 클립보드에 텍스트가 없을 경우 무시
    return 'break'

# 텍스트 전체 선택 기능 추가
def select_all(event, widget):
    widget.tag_add(tk.SEL, "1.0", tk.END)
    widget.mark_set(tk.INSERT, "1.0")
    widget.see(tk.INSERT)
    return 'break'  # 기본 이벤트 처리 방지

# GUI 시작
if __name__ == "__main__":
    start_gui()
