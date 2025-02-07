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
from rembg import remove
from fastapi.responses import StreamingResponse

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
def generate_image_mid_test(prompt: str):
    try:
        prompt = f"{prompt}"

        USE_API_TOKEN = os.getenv("USE_API_TOKEN")
        DIS_USE_TOKEN = os.getenv("DIS_USE_TOKEN")
        DIS_SER_ID = os.getenv("DIS_SER_ID")
        DIS_CHA_ID = os.getenv("DIS_CHA_ID")

        if not (USE_API_TOKEN and DIS_USE_TOKEN and DIS_SER_ID and DIS_CHA_ID):
            raise ValueError("One or more required environment variables are missing.")

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

        # Step 1: Job creation
        response = requests.post(apiUrl, headers=headers, json=body)
        print(response)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        job_id = response.json().get("jobid")
        if not job_id:
            raise ValueError("No job ID returned from API")

        # Step 2: Polling to check job status
        apiUrl = f"https://api.useapi.net/v2/jobs/?jobid={job_id}"
        timeout_seconds = 180  # 최대 120초 동안 대기
        start_time = time.time()

        while True:
            response = requests.get(apiUrl, headers=headers)
            response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

            data = response.json()
            status = data.get("status")

            if status == "completed":
                break  # 작업 완료
            elif status in ["failed", "canceled"]:
                raise RuntimeError(f"Job failed or canceled with status: {status}")

            # 작업이 완료되지 않은 경우 대기 후 재요청
            elapsed_time = time.time() - start_time
            if elapsed_time >= timeout_seconds:
                raise TimeoutError(f"Job polling exceeded maximum timeout of {timeout_seconds} seconds.")

            print(f"Job not ready yet, retrying in 5 seconds... (Elapsed time: {int(elapsed_time)}s/{timeout_seconds}s)")
            time.sleep(5)

        link = data.get("attachments")
        if not link or len(link) == 0:
            raise ValueError("No attachments found in job response")

        # Step 3: Image download
        url = link[0]['proxy_url']
        image_response = requests.get(url)
        image_response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

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

    except requests.exceptions.RequestException as e:
        return {"error": f"HTTP 요청 중 오류 발생: {e}"}
    except ValueError as e:
        return {"error": f"값 오류 발생: {e}"}
    except RuntimeError as e:
        return {"error": f"실행 오류 발생: {e}"}
    except Exception as e:
        return {"error": f"알 수 없는 오류 발생: {e}"}

def generate_image_remove_bg(image):
    try:
        # Pixian API에 파일 직접 전송
        response = requests.post(
            'https://api.pixian.ai/api/v2/remove-background',
            files={"image": (image.filename, image.file, image.content_type)},
            data={
                'test': 'true'  # TODO: Remove for production
            },
            auth=('pxjrefqwqgdapzl', 'on8deo8fidgmljosuae5h6nb8l39s5iiv043v9nke6rtdklhj4ea')
        )

        # 요청이 성공하면 Pixian에서 반환된 이미지 저장
        if response.status_code == requests.codes.ok:
            return StreamingResponse(io.BytesIO(response.content), media_type="image/png")
        else:
            return {"error": f"Pixian API 오류: {response.status_code} - {response.text}"}

    except Exception as e:
        return {"error": str(e)}
    

def generate_image_remove_bg_free(image):
    output_image = remove(image)

    # 메모리에서 바로 반환 (저장 X)
    img_io = io.BytesIO()
    output_image.save(img_io, format="PNG")
    img_io.seek(0)  # 스트림의 시작 위치로 이동

    return StreamingResponse(img_io, media_type="image/png")