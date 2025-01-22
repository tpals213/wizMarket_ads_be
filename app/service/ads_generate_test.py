import logging
import io
import os
from dotenv import load_dotenv
import requests
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO
import base64
import re
import time
from runwayml import RunwayML
import anthropic
from moviepy import *
import uuid

logger = logging.getLogger(__name__)
load_dotenv()

# OpenAI API 키 설정
api_key = os.getenv("GPT_KEY")
client = OpenAI(api_key=api_key)


def generate_image_stable(prompt: str,):
    token = os.getenv("FACE_KEY")


    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"inputs": prompt}
    # API 요청 보내기
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()  # 에러 발생 시 예외 처리

        image = Image.open(BytesIO(response.content))
        # 이미지를 Base64로 인코딩
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {"image": f"data:image/png;base64,{base64_image}"}

    except requests.exceptions.RequestException as e:
        print(f"Failed to generate image: {e}")
        return {"error": str(e)}


# 달리 이미지 생성
def generate_image_dalle(prompt: str,):

    try:
        # Prompt 전달 및 이미지 생성
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="hd", 
            n=1
        )
        image_url = response.data[0].url
        # print(image_url)
        # 이미지 다운로드
        image_response = requests.get(image_url)
        image_response.raise_for_status()
        # 이미지 열기
        image = Image.open(io.BytesIO(image_response.content))

        # 이미지를 Base64로 인코딩
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {"image": f"data:image/png;base64,{base64_image}"}
        
    except Exception as e:
        return {"error": f"이미지 생성 중 오류 발생: {e}"}
    

# 미드저니 이미지 생성
def generate_image_mid(prompt):
    prompt = f"{prompt} {16:9}"

    USE_API_TOKEN = os.getenv("USE_API_TOKEN")
    DIS_USE_TOKEN = os.getenv("DIS_USE_TOKEN")
    DIS_SER_ID = os.getenv("DIS_SER_ID")
    DIS_CHA_ID = os.getenv("DIS_CHA_ID")

    apiUrl = "https://api.useapi.net/v2/jobs/imagine"
    token = USE_API_TOKEN
    discord = DIS_USE_TOKEN
    server = DIS_SER_ID
    channel = DIS_CHA_ID
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    body = {
        "prompt": f"{prompt}",
        "discord": f"{discord}",
        "server": f"{server}",
        "channel": f"{channel}"
    }
    response = requests.post(apiUrl, headers=headers, json=body)
    if response.status_code != 200:
        return {"error": f"Job creation failed with status {response.status_code}"}

    job_id = response.json().get("jobid")
    if not job_id:
        return {"error": "No job ID returned from API"}

    # Step 2: Polling to check job status
    apiUrl = f"https://api.useapi.net/v2/jobs/?jobid={job_id}"
    while True:
        response = requests.get(apiUrl, headers=headers)
        if response.status_code != 200:
            return {"error": f"Job status check failed with status {response.status_code}"}
        
        data = response.json()
        status = data.get("status")
        if status == "completed":
            break  # 작업 완료
        elif status in ["failed", "canceled"]:
            return {"error": f"Job failed or canceled with status: {status}"}
        
        # 작업이 완료되지 않은 경우 대기 후 재요청
        print("Job not ready yet, retrying in 5 seconds...")
        time.sleep(5)  # 5초 대기

    link = data.get("attachments")

    if link and len(link) > 0:
        url = link[0]['proxy_url']  # 이미지 URL 가져오기

        # 이미지 다운로드
        image_response = requests.get(url)
        if image_response.status_code == 200:
            image = Image.open(BytesIO(image_response.content))
            width, height = image.size

            # 자를 좌표 설정
            coordinates = [
                (0, 0, width // 2, height // 2),       # 왼쪽 상단
                (width // 2, 0, width, height // 2),   # 오른쪽 상단
                (0, height // 2, width // 2, height),  # 왼쪽 하단
                (width // 2, height // 2, width, height)  # 오른쪽 하단
            ]

            # 잘린 이미지를 Base64로 변환하여 리스트 생성
            base64_images = []
            for coord in coordinates:
                cropped_image = image.crop(coord)  # 자른 이미지

                # 이미지 Base64 변환
                buffer = BytesIO()
                cropped_image.save(buffer, format="PNG")
                buffer.seek(0)
                base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
                base64_images.append(f"data:image/png;base64,{base64_image}")

            # Base64 이미지 리스트 반환
            return {"images": base64_images}
        else:
            return {"error": "Failed to download image from proxy URL"}
    else:
        return {"error": "No attachments found in job response"}
