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


# 문구 생성
def generate_content(
    prompt, gpt_role, detail_content
):
    
    # gpt 영역
    gpt_content = gpt_role
    content = prompt + '\n내용 : ' + detail_content
    client = OpenAI(api_key=os.getenv("GPT_KEY"))
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": gpt_content},
            {"role": "user", "content": content},
        ],
    )
    report = completion.choices[0].message.content
    return report

# 신 문구 생성
def generate_new_content(
    prompt
):
    # gpt 영역
    content = prompt
    client = OpenAI(api_key=os.getenv("GPT_KEY"))
    completion = client.chat.completions.create(
        model="o1-preview",
        messages=[
            {"role": "user", "content": content}
        ],
    )
    report = completion.choices[0].message.content
    # print(report)
    return report


# 구 문구 생성
def generate_old_content(
    prompt
):
    # gpt 영역
    content = prompt
    client = OpenAI(api_key=os.getenv("GPT_KEY"))
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": content},
        ],
    )
    report = completion.choices[0].message.content
    return report

# 클로드 문구 생성
def generate_claude_content(
    prompt
):
    api_key = os.getenv("CLAUDE_KEY")
    client = anthropic.Anthropic(api_key=api_key)

    result_text = ""
    response = client.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1000,
        temperature=0.0,
        system="Respond only in Korean.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    if not response.content or not isinstance(response.content, list):
        result_text = "No response or unexpected response format."
    else:
        response_texts = [block.text for block in response.content if hasattr(block, 'text')]
        result_text = " ".join(response_texts)
 
    return result_text



# OpenAI API 키 설정
api_key = os.getenv("GPT_KEY")
client = OpenAI(api_key=api_key)

# 미드저니 이미지 생성
def generate_image_mid(
    use_option, ai_prompt
):
    use_option_propt_map = {
        '문자메시지': (9, 16),
        '유튜브 썸네일': (16, 9),
        '인스타그램 스토리': (1024, 1792),
        '인스타그램 피드': (1, 1),
        '배너': (16, 9),
        '네이버 블로그': (9, 16)
    }
    # gpt 영역
    gpt_content = """
        You are now a Midjourney prompt engineer.
        Midjourney AI creates images based on given prompts.
        Please refer to the link below for Midjourney.
        https://en.wikipedia.org/wiki/Midjourney
        All you have to do is configure the prompt so Midjourney can generate the best image for what you're requesting.
    """
    content = ai_prompt
    client = OpenAI(api_key=os.getenv("GPT_KEY"))
    completion = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.7,
        messages=[
            {"role": "system", "content": gpt_content},
            {"role": "user", "content": f"Translate the following into English and create a MidJourney prompt: {content}"},
        ],
    )
    prompt_re = completion.choices[0].message.content 

    # Get aspect ratio from use_option
    aspect_ratio = use_option_propt_map.get(use_option)
    if not aspect_ratio:
        raise ValueError("Invalid `use_option` provided.")

    # Format --ar string dynamically
    ar_str = f"--ar {aspect_ratio[0]}:{aspect_ratio[1]}"
    # style_str = f"artgerm"
    # without_text = f"without text"

    # Combine prompt with aspect ratio
    # prompt = f"{prompt_re} {without_text} {style_str} {ar_str}"
    prompt = f"{prompt_re} {ar_str}"

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
    print(job_id)
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

            # 잘린 이미지 객체 리스트 생성
            img_parts = []
            for coord in coordinates:
                cropped_image = image.crop(coord)  # 자른 이미지
                img_parts.append(cropped_image)  # 리스트에 추가

            # 잘린 이미지 객체 리스트 반환
            return {"images": img_parts}
        else:
            return {"error": "Failed to download image from proxy URL"}
    else:
        return {"error": "No attachments found in job response"}



# 이미지 생성
def generate_image(
    use_option, korean_image_prompt
):
    
    # gpt 영역
    gpt_content = """
        당신은 전문 번역가입니다. 사용자가 제공한 내용을 정확히 영어로 번역하세요. 번역 외의 부가적인 설명이나 추가적인 내용을 작성하지 마세요.
    """    
    content = korean_image_prompt
    client = OpenAI(api_key=os.getenv("GPT_KEY"))
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": gpt_content},
            {"role": "user", "content": content},
        ],
    )
    english_image_prompt = completion.choices[0].message.content

    # token = os.getenv("FACE_KEY")
    # if model_option == 'basic':
    #     # print(prompt)
    #     API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large"
    #     headers = {"Authorization": f"Bearer {token}"}
    #     data = {"inputs": prompt}
    #     # API 요청 보내기
    #     try:
    #         # API 요청 보내기
    #         response = requests.post(API_URL, headers=headers, json=data)
    #         response.raise_for_status()  # 에러 발생 시 예외 처리

    #         # 응답 바이너리 데이터를 PIL 이미지로 변환
    #         image = Image.open(BytesIO(response.content))

    #         if resize:
    #             target_width = resize[0]  # 원하는 가로 크기
    #             original_width, original_height = image.size
    #             aspect_ratio = original_height / original_width  # 세로/가로 비율 계산

    #             # 새로운 세로 크기 계산
    #             target_height = int(target_width * aspect_ratio)

    #             # 리사이즈 수행
    #             image = image.resize((target_width, target_height), Image.LANCZOS)

    #         # 이미지를 Base64로 인코딩
    #         buffered = BytesIO()
    #         image.save(buffered, format="PNG")  # PNG 형식으로 저장
    #         img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    #         image_list.append(f"data:image/png;base64,{img_str}")
    #         # JSON 형식으로 Base64 이미지 반환
    #         return {"image": image_list}

    #     except requests.exceptions.RequestException as e:
    #         print(f"Failed to generate image: {e}")
    #         return {"error": str(e)}
        
    try:
        # Resize와 Final Size 매핑
        resize_mapping = {
            '카카오톡': (1024, 1792),
            '유튜브 썸네일': (1792, 1024),
            '인스타그램 스토리': (1024, 1792),
            '인스타그램 피드': (1024, 1024),
            '네이버 블로그': (1792, 1024)
        }
        resize = resize_mapping.get(use_option, None)

        if not resize:
            raise ValueError("Invalid `use_option` provided or no resize option available.")

        resize_str = f"{resize[0]}x{resize[1]}"
        
        # Prompt 전달 및 이미지 생성
        response = client.images.generate(
            model="dall-e-3",
            prompt=english_image_prompt,
            size=resize_str,
            quality="hd", 
            n=1
        )
        image_url = response.data[0].url
        print(image_url)
        # 이미지 다운로드
        image_response = requests.get(image_url)
        image_response.raise_for_status()

        # 이미지 열기
        img = Image.open(io.BytesIO(image_response.content))

        return [img]
        
    except Exception as e:
        return {"error": f"이미지 생성 중 오류 발생: {e}"}


# 영상 생성
def generate_video(file_path):

    ROOT_PATH = os.getenv("ROOT_PATH")
    AUDIO_PATH = os.getenv("AUDIO_PATH")
    full_audio_path = os.path.join(ROOT_PATH, AUDIO_PATH.strip("/"), "audio.mp3")

    api_key = os.getenv("RUNWAYML_API_SECRET")

    if not api_key:
        raise ValueError("API key not found. Please check your .env file.")

    # Initialize the RunwayML client with the API key
    client = RunwayML(api_key=api_key)

    image_path = file_path

    # Encode image to base64
    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")

    try : 
        # Create a new image-to-video task
        task = client.image_to_video.create(
            model='gen3a_turbo',
            prompt_image=f"data:image/png;base64,{base64_image}",
            prompt_text='Make the subject of the image move vividly.',
        )
        task_id = task.id
    except Exception as e:
        print(e)

    # Poll the task until it's complete
    print("Task created. Polling for status...")
    while True:
        task = client.tasks.retrieve(task_id)
        if task.status in ['SUCCEEDED', 'FAILED']:
            break
        print(f"Task status: {task.status}. Retrying in 10 seconds...")
        time.sleep(10)

    # Check final status
    if task.status == 'SUCCEEDED':
        if os.path.exists(file_path):
            os.remove(file_path)
        result_url = task.output[0]  # output is a list, so take the first element

        video_file_path = "output.mp4"
        response = requests.get(result_url, stream=True)

        with open(video_file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        audio_path = full_audio_path

        VIDEO_PATH = os.getenv("VIDEO_PATH")
        output_path = os.path.join(ROOT_PATH, VIDEO_PATH.strip("/"), "video_with_audio.mp4")
        return_path = os.path.join(VIDEO_PATH, "video_with_audio.mp4")
        client_path = return_path.replace("/app", "")
        # output_path = "video_with_audio.mp4"
        video = VideoFileClip(video_file_path)
        audio = AudioFileClip(audio_path).subclipped(0, video.duration)
        video_with_audio = video.with_audio(audio)
        video_with_audio.write_videofile(output_path, codec="libx264", audio_codec="aac")

        # Close resources
        video.close()
        audio.close()
        video_with_audio.close()

        return {"result_url": client_path}
    else:
        print("Task failed.")
        # Log failure details
        print(f"Failure Reason: {task.failure}")
        print(f"Failure Code: {task.failure_code}")