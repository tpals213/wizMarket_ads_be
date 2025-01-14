from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
import cv2
from instagrapi import Client
import logging
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO
from typing import List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import pymysql
from openpyxl import load_workbook
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from datetime import datetime
import os, time
import base64
from concurrent.futures import ThreadPoolExecutor
import pymysql
from moviepy import *


logger = logging.getLogger(__name__)
load_dotenv()

# OpenAI API 키 설정
api_key = os.getenv("GPT_KEY")
client = OpenAI(api_key=api_key)


INSTA_NAME = os.getenv("INSTA_NAME")
INSTA_PW = os.getenv("INSTA_PW")


# 인스타 테스트
def test_insta():
    cl = Client()
    cl.login(INSTA_NAME, INSTA_PW)
    user_id = cl.user_id_from_username(INSTA_NAME)
    medias = cl.user_medias(user_id, 20)
    print(medias)

# ADS 인스타 스토리 업로드
def upload_story_ads(content, file_path):
    try:
        cl = Client()
        cl.login(INSTA_NAME, INSTA_PW)
        cl.photo_upload_to_story(file_path, content)
        # 업로드 성공 후 파일 삭제
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"파일 삭제 완료: {file_path}")
    except Exception as e:
        print(f"스토리 업로드 중 오류가 발생했습니다: {e}")

# ADS 인스타 피드 업로드
def upload_feed_ads(content, file_path):
    try:
        cl = Client()
        cl.login(INSTA_NAME, INSTA_PW)
        cl.photo_upload(file_path, content)
        # 업로드 성공 후 파일 삭제
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"파일 삭제 완료: {file_path}")
    except Exception as e:
        print(f"피드 업로드 중 오류가 발생했습니다: {e}")


# ADS 이메일 전송
async def upload_mms_ads(content: str, file_path: str):
    try:
        # 환경 변수에서 이메일 정보 가져오기
        mail_from = os.getenv("MAIL_FROM")
        mail_to = os.getenv("MAIL_TO")
        mail_pw = os.getenv("MAIL_PW")

        # 이메일 설정
        msg = MIMEMultipart()
        msg['From'] = mail_from
        msg['To'] = mail_to
        msg['Subject'] = "광고 입니다."

        # 이메일 본문 추가
        msg.attach(MIMEText(content, 'plain'))

        # 파일 첨부
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={os.path.basename(file_path)}'
                )
                msg.attach(part)
        else:
            print("첨부 파일 없이 이메일을 전송합니다.")

        # SMTP 서버 설정
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()  # TLS 시작
            server.login(mail_from, mail_pw)  # 로그인
            server.sendmail(mail_from, mail_to, msg.as_string())  # 이메일 전송

    except Exception as e:
        print(f"이메일 전송 중 오류 발생: {e}")


ROOT_PATH = os.getenv("ROOT_PATH")
AUTH_PATH = os.getenv("AUTH_PATH")
AUDIO_PATH = os.getenv("AUDIO_PATH")
full_audio_path = os.path.join(ROOT_PATH, AUDIO_PATH.strip("/"), "audio.mp3")


# ADS 유튜브 업로드
# 인증
def get_authenticated_service():
    # InstalledAppFlow를 사용하여 OAuth 인증 수행
    # CLIENT_SECRETS_FILE = os.path.join(ROOT_PATH, AUTH_PATH.lstrip("/"), "google_auth.json")
    CLIENT_SECRETS_FILE = os.path.join(ROOT_PATH, AUTH_PATH.lstrip("/"), "google_auth_wiz.json")
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, SCOPES
    )
    # 로컬 서버를 실행하여 인증을 수행
    credentials = flow.run_local_server(port=8080, prompt="consent", authorization_prompt_message="")
    return build("youtube", "v3", credentials=credentials)

# 업로드
def upload_video(youtube, file, title, description, tags, category_id):
    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": "public"  # 공개 여부: "private", "unlisted", "public"
        }
    }

    media_file = MediaFileUpload(file, chunksize=-1, resumable=True)
    response = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media_file
    ).execute()


# 사진 영상 변환
def upload_youtube_ads(content, store_name, tag, file_path):
    # 이미지 파일 경로
    img_file = file_path

    # 이미지 불러오기
    img = cv2.imread(img_file)
    if img is None:
        print(f"이미지를 불러올 수 없습니다: {img_file}")
        return
    
    # 이미지의 크기 가져오기 (가로, 세로)
    height, width, _ = img.shape
    frame_size = (width, height)  # 이미지 크기를 그대로 사용


    fps = 24  # 초당 프레임
    duration = 5  # 동영상 길이 (초)

    # 생성될 동영상 경로
    video_file_path = "output.mp4"

    # 비디오 코덱 설정 및 VideoWriter 초기화
    out = cv2.VideoWriter(video_file_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, frame_size)

    # 동영상 길이와 FPS에 따라 총 프레임 수 계산
    total_frames = fps * duration

    # 동일한 이미지를 여러 프레임으로 작성
    for _ in range(total_frames):
        out.write(img)

    out.release()

    audio_path = full_audio_path
    output_path = "video_with_audio.mp4"
    video = VideoFileClip(video_file_path)
    audio = AudioFileClip(audio_path).subclipped(0, video.duration)
    video_with_audio = video.with_audio(audio)
    video_with_audio.write_videofile(output_path, codec="libx264", audio_codec="aac")

    try:
        # YouTube 업로드
        youtube_service = get_authenticated_service()
        upload_video(
            youtube=youtube_service,
            file=output_path,  # 업로드할 동영상 경로
            title=store_name,  # 동영상 제목
            description=content,  # 동영상 설명
            tags=[tag],  # 태그
            category_id="22"  # 카테고리 ID (22: People & Blogs)
        )


        # 업로드 성공 시 파일 삭제
        if os.path.exists(video_file_path):
            os.remove(file_path)
            os.remove(video_file_path)
            os.remove(output_path)
            print(f"동영상 파일 삭제 완료: {video_file_path}")

    except Exception as e:
        print(f"업로드 중 오류 발생: {e}")
        if os.path.exists(video_file_path):
            print(f"동영상 파일을 삭제하지 않았습니다: {video_file_path}")



def upload_naver_ads():
    # 글로벌 드라이버 설정
    options = Options()
    options.add_argument("--start-fullscreen")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--user-data-dir=C:/Users/jyes_semin/AppData/Local/Google/Chrome/User Data")  # Chrome 사용자 데이터 경로
    options.add_argument("--profile-directory=Profile 5")  # 프로필 이름 (기본값은 'Default')


    # WebDriver Manager를 이용해 ChromeDriver 자동 관리
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    

    try:
        # 네이버 블로그 홈 페이지로 이동
        driver.get("https://section.blog.naver.com/BlogHome.naver?directoryNo=0&currentPage=1&groupId=0")
        time.sleep(5)  # 페이지 로드 대기

        

    except Exception as e:
        print(f"오류 발생: {e}")

    finally:
        driver.quit()


if __name__ == "__main__":
    test_insta()