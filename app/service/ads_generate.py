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
        '인스타그램 스토리': (9, 16),
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

        # 이미지 저장 및 Base64 인코딩
        image_response = requests.get(url)
        if image_response.status_code == 200:
            image = Image.open(BytesIO(image_response.content))
            width, height = image.size

            coordinates = [
                (0, 0, width // 2, height // 2),       # 왼쪽 상단
                (width // 2, 0, width, height // 2),   # 오른쪽 상단
                (0, height // 2, width // 2, height),  # 왼쪽 하단
                (width // 2, height // 2, width, height)  # 오른쪽 하단
            ]

            img_parts_base64 = []
            for coord in coordinates:
                cropped_image = image.crop(coord)
                buffered = BytesIO()
                cropped_image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                img_parts_base64.append(f"data:image/png;base64,{img_str}")

            # 결과 반환
            return {"image": img_parts_base64}
        else:
            return {"error": "Failed to download image from proxy URL"}
    else:
        return {"error": "No attachments found in job response"}



# 이미지 생성
def generate_image(
    use_option, model_option, ai_prompt
):
    if use_option == '문자메시지':
        resize = (333, 458)
    elif use_option == '유튜브 썸네일':
        resize = (412, 232)
    elif use_option == '인스타그램 스토리':
        resize = (412, 732)
    elif use_option == '인스타그램 피드':
        resize = (412, 514)
    elif use_option == '배너':
        resize = (377, 377)
    else :
        resize= None

    # gpt 영역
    gpt_content = """
        당신은 전문 번역가입니다. 사용자가 제공한 내용을 정확히 영어로 번역하세요. 번역 외의 부가적인 설명이나 추가적인 내용을 작성하지 마세요.
    """    
    content = ai_prompt
    client = OpenAI(api_key=os.getenv("GPT_KEY"))
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": gpt_content},
            {"role": "user", "content": content},
        ],
    )
    prompt = completion.choices[0].message.content
    image_list = []
    token = os.getenv("FACE_KEY")
    if model_option == 'basic':
        # print(prompt)
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-3.5-large"
        headers = {"Authorization": f"Bearer {token}"}
        data = {"inputs": prompt}
        # API 요청 보내기
        try:
            # API 요청 보내기
            response = requests.post(API_URL, headers=headers, json=data)
            response.raise_for_status()  # 에러 발생 시 예외 처리

            # 응답 바이너리 데이터를 PIL 이미지로 변환
            image = Image.open(BytesIO(response.content))

            if resize:
                target_width = resize[0]  # 원하는 가로 크기
                original_width, original_height = image.size
                aspect_ratio = original_height / original_width  # 세로/가로 비율 계산

                # 새로운 세로 크기 계산
                target_height = int(target_width * aspect_ratio)

                # 리사이즈 수행
                image = image.resize((target_width, target_height), Image.LANCZOS)

            # 이미지를 Base64로 인코딩
            buffered = BytesIO()
            image.save(buffered, format="PNG")  # PNG 형식으로 저장
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            image_list.append(f"data:image/png;base64,{img_str}")
            # JSON 형식으로 Base64 이미지 반환
            return {"image": image_list}

        except requests.exceptions.RequestException as e:
            print(f"Failed to generate image: {e}")
            return {"error": str(e)}
        
    elif model_option == 'poster':
        API_URL = "https://api-inference.huggingface.co/models/alex1105/movie-posters-v2"
        headers = {"Authorization": f"Bearer {token}"}
        data = {"inputs": prompt}
        # API 요청 보내기
        try:
            # API 요청 보내기
            response = requests.post(API_URL, headers=headers, json=data)
            response.raise_for_status()  # 에러 발생 시 예외 처리

            # 응답 바이너리 데이터를 PIL 이미지로 변환
            image = Image.open(BytesIO(response.content))

            # 이미지 리사이즈
            if resize:
                target_width = resize[0]  # 원하는 가로 크기
                original_width, original_height = image.size
                aspect_ratio = original_height / original_width  # 세로/가로 비율 계산

                # 새로운 세로 크기 계산
                target_height = int(target_width * aspect_ratio)

                # 리사이즈 수행
                image = image.resize((target_width, target_height), Image.LANCZOS)

            # 이미지를 Base64로 인코딩
            buffered = BytesIO()
            image.save(buffered, format="PNG")  # PNG 형식으로 저장
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

            # JSON 형식으로 Base64 이미지 반환
            return {"image": f"data:image/png;base64,{img_str}"}

        except requests.exceptions.RequestException as e:
            print(f"Failed to generate image: {e}")
            return {"error": str(e)}
        
    elif model_option == 'food':
        API_URL = "https://api-inference.huggingface.co/models/its-magick/merlin-food"
        headers = {"Authorization": f"Bearer {token}"}
        data = {"inputs": prompt}
        # API 요청 보내기
        # 응답 처리
        try:
            # API 요청 보내기
            response = requests.post(API_URL, headers=headers, json=data)
            response.raise_for_status()  # 에러 발생 시 예외 처리

            # 응답 바이너리 데이터를 PIL 이미지로 변환
            image = Image.open(BytesIO(response.content))

            # 이미지 리사이즈
            if resize:
                target_width = resize[0]  # 원하는 가로 크기
                original_width, original_height = image.size
                aspect_ratio = original_height / original_width  # 세로/가로 비율 계산

                # 새로운 세로 크기 계산
                target_height = int(target_width * aspect_ratio)

                # 리사이즈 수행
                image = image.resize((target_width, target_height), Image.LANCZOS)

            # 이미지를 Base64로 인코딩
            buffered = BytesIO()
            image.save(buffered, format="PNG")  # PNG 형식으로 저장
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

            # JSON 형식으로 Base64 이미지 반환
            return {"image": f"data:image/png;base64,{img_str}"}

        except requests.exceptions.RequestException as e:
            print(f"Failed to generate image: {e}")
            return {"error": str(e)}
        
    elif model_option == 'dalle':
        try:
            # Resize와 Final Size 매핑
            resize_mapping = {
                '문자메시지': (1024, 1792),
                '유튜브 썸네일': (1792, 1024),
                '인스타그램 스토리': (1024, 1792),
                '인스타그램 피드': (1024, 1024),
                '배너': (1792, 1024),
                '네이버 블로그': (1792, 1024)
            }
            resize = resize_mapping.get(use_option, None)

            if not resize:
                raise ValueError("Invalid `use_option` provided or no resize option available.")

            resize_str = f"{resize[0]}x{resize[1]}"
            
            # Prompt 전달 및 이미지 생성
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=resize_str,
                quality="hd", 
                n=1
            )
            image_url = response.data[0].url

            # 이미지 다운로드
            image_response = requests.get(image_url)
            image_response.raise_for_status()

            # 이미지 열기
            img = Image.open(io.BytesIO(image_response.content))

             # Base64 인코딩
            buffer = io.BytesIO()
            img = Image.open(io.BytesIO(image_response.content))
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
            image_list.append(f"data:image/png;base64,{img_str}")

            return {"image": image_list}
        
        except Exception as e:
            return {"error": f"이미지 생성 중 오류 발생: {e}"}









def split_top_line(text, max_length):
    """
    입력된 text를 8글자를 기준으로 반복적으로 나눔.
    - text가 8글자 이하일 경우, 그대로 반환.
    - text가 8글자 초과일 경우, 띄어쓰기 기준으로 나눠 반환하며 각 줄은 max_length를 넘지 않음.
    """
    result = []
    words = text.split()

    current_line = []
    current_length = 0

    for word in words:
        word_length = len(word)
        # 현재 줄에 추가해도 max_length를 넘지 않으면 추가
        if current_length + word_length + (1 if current_line else 0) <= max_length:
            current_line.append(word)
            current_length += word_length + (1 if current_line else 0)
        else:
            # 현재 줄이 꽉 찼으면 result에 추가하고 새로운 줄 시작
            result.append(" ".join(current_line))
            current_line = [word]
            current_length = word_length

    # 마지막 줄 추가
    if current_line:
        result.append(" ".join(current_line))

    return result


def combine_ads (store_name, road_name, content, image_width, image_height, image, alignment="center"):
    image_1 = combine_ads_ver1(store_name, road_name, content, image_width, image_height, image, alignment="center")
    image_2 = combine_ads_ver2(store_name, road_name, content, image_width, image_height, image, alignment="center")
    return (image_1, image_2)

# 주제 + 문구 + 이미지 합치기
def combine_ads_ver1(store_name, road_name, content, image_width, image_height, image, alignment="center"):
    root_path = os.getenv("ROOT_PATH", ".")
    sp_image_path = os.path.join(root_path, "app", "static", "images", "BG_snow.png") 
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 검은 바탕 생성 및 합성
    black_overlay = Image.new("RGBA", (image_width, image_height), (0, 0, 0, int(255 * 0.4)))  # 검은 바탕(60% 투명도)

    image = Image.alpha_composite(image, black_overlay)

    # sp_image 불러오기 및 리사이즈
    sp_image = Image.open(sp_image_path).convert("RGBA")
    original_width, original_height = sp_image.size

    # sp_image의 가로 길이를 기존 이미지의 가로 길이에 맞추고, 세로는 비율에 맞게 조정
    new_width = image_width
    new_height = int((new_width / original_width) * original_height)
    sp_image = sp_image.resize((new_width, new_height))
    # 투명도 조정
    alpha = sp_image.split()[3]  # RGBA의 알파 채널 추출
    alpha = ImageEnhance.Brightness(alpha).enhance(0.8)  # 투명도를 0.6으로 조정
    sp_image.putalpha(alpha)  # 수정된 알파 채널을 다시 이미지에 적용

    # sp_image에 투명한 배경 추가하여 기존 이미지와 크기 맞춤
    padded_sp_image = Image.new("RGBA", (image_width, image_height), (0, 0, 0, 0))  # 투명 배경 생성
    # sp_image 배치
    offset_x = 0  # 기본 가로 정렬: 좌측
    if alignment == "center":
        offset_x = (image_width - new_width) // 2
    elif alignment == "right":
        offset_x = image_width - new_width

    offset_y = (image_height - new_height) // 2  # 세로 중앙 배치
    padded_sp_image.paste(sp_image, (offset_x, offset_y))  # sp_image를 배경 위에 붙임

    # sp_image와 기존 이미지 합성
    image = Image.alpha_composite(image.convert("RGBA"), padded_sp_image)

    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "JalnanGothicTTF.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "BMHANNA_11yrs_ttf.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    top_font_size = image_width / 10
    bottom_font_size = (top_font_size * 5) / 8
    store_name_font_size = image_width / 20
    road_name_font_size = image_width / 22

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # 텍스트를 '<br>'로 구분하여 줄 나누기
    # lines = content.split(' ')
    # lines = [re.sub(r'<[^>]+>', '', line).replace('\r', '').replace('\n', '') for line in lines]
    lines = re.split(r'[.!?,\n]', content)  # 구두점, 쉼표, 줄바꿈 모두 처리
    lines = [line.strip() for line in lines if line.strip()]
    if len(lines) > 0:
        top_line = lines[0].strip()
        lines_list = split_top_line(top_line, max_length=8)  # 반환값은 리스트
        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = image_height / 10
        # 반복적으로 각 줄 렌더링
        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비 계산
                top_text_width = top_font.getbbox(line)[2]
                # 중앙 정렬 X 좌표 계산
                top_text_x = (image_width - top_text_width) // 2
                # 현재 줄 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill=(255, 255, 255, int(255 * 0.8)))
                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5

    # 하단 텍스트 추가
    bottom_lines = lines[1:]  # 첫 번째 줄을 제외한 나머지
    line_height = bottom_font.getbbox("A")[3] + 3
    text_y = (image_height * 3) // 5

    for line in bottom_lines:
        line = line.strip()
        # 하단 줄을 분리하여 20자 이상일 경우 나눔
        split_lines = split_top_line(line, max_length=20)

        for sub_line in split_lines:
            sub_line = sub_line.strip()
            text_width = bottom_font.getbbox(sub_line)[2]

            if alignment == "center":
                text_x = (image_width - text_width) // 2
            elif alignment == "left":
                text_x = 10
            elif alignment == "right":
                text_x = image_width - text_width - 10
            else:
                raise ValueError("Invalid alignment option. Choose 'center', 'left', or 'right'.")

            # 현재 줄 렌더링
            draw.text((text_x, text_y), sub_line, font=bottom_font, fill="#03FF57")
            text_y += line_height  # 다음 줄로 이동

    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_x = (image_width - store_name_width) // 2
    store_name_y = image_height - (image_height / 7) # 분모가 작을수록 하단에 더 멀게
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="white")

    # road_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_x = (image_width - road_name_width) // 2
    road_name_y = image_height - (image_height / 10) # 분모가 작을수록 하단에 더 멀게
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill="white")

    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"


def combine_ads_ver2(store_name, road_name, content, image_width, image_height, image, alignment="center"):
    root_path = os.getenv("ROOT_PATH", ".")
    sp_image_path = os.path.join(root_path, "app", "static", "images", "new_imo.png") 
    
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 검은 바탕 생성 및 합성
    black_overlay = Image.new("RGBA", (image_width, image_height), (0, 0, 0, int(255 * 0.4)))  # 검은 바탕(60% 투명도)
    image = Image.alpha_composite(image, black_overlay)

    # sp_image 불러오기 및 리사이즈
    sp_image = Image.open(sp_image_path).convert("RGBA")
    original_width, original_height = sp_image.size

    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = int(image_width / 4)
    new_height = int((new_width / original_width) * original_height)
    sp_image = sp_image.resize((new_width, new_height))

    # 4번 위치 (하단 오른쪽) 중심 좌표 계산
    offset_x = (image_width * 3 // 4) - (new_width // 2)  # 4등분 했을 때 하단 오른쪽 중심 X
    offset_y = (image_height * 3 // 4) - (new_height // 2)  # 4등분 했을 때 하단 오른쪽 중심 Y

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(sp_image, (offset_x, offset_y), sp_image)

    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "JalnanGothicTTF.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "BMHANNA_11yrs_ttf.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    top_font_size = image_width / 20
    bottom_font_size = image_width / 10
    store_name_font_size = image_width / 24
    road_name_font_size = image_width / 26

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    # 텍스트를 '<br>'로 구분하여 줄 나누기
    # lines = content.split(' ')
    # lines = [re.sub(r'<[^>]+>', '', line).replace('\r', '').replace('\n', '') for line in lines]
    lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
    lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외
    if len(lines) > 0:
        top_line = lines[0].strip()
        lines_list = split_top_line(top_line, max_length=10)  # 반환값은 리스트

        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = image_height / 10
        line_padding = 5  # 텍스트와 선 사이의 패딩

        # 반복적으로 각 줄 렌더링
        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비 계산
                top_text_width = top_font.getbbox(line)[2]
                top_text_height = top_font.getbbox(line)[3]  # 텍스트 높이 계산
                # 중앙 정렬 X 좌표 계산
                top_text_x = (image_width - top_text_width) // 2

                # 텍스트 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill=(255, 255, 255, int(255 * 0.8)))

                # 첫 번째 줄에 윗줄 추가
                if i == 0:
                    line_start_x = top_text_x
                    line_end_x = top_text_x + top_text_width
                    draw.line(
                        [(line_start_x, top_text_y - line_padding),
                        (line_end_x, top_text_y - line_padding)],
                        fill=(255, 255, 255, int(255 * 0.8)),
                        width=2
                    )

                # 마지막 줄에 밑줄 추가
                if i == len(lines_list) - 1:
                    line_start_x = top_text_x
                    line_end_x = top_text_x + top_text_width
                    draw.line(
                        [(line_start_x, top_text_y + top_text_height + line_padding),
                        (line_end_x, top_text_y + top_text_height + line_padding)],
                        fill=(255, 255, 255, int(255 * 0.8)),
                        width=2
                    )

                # Y 좌표를 다음 줄로 이동
                top_text_y += top_text_height + 2 * line_padding



    # 하단 텍스트 추가
    bottom_lines = lines[1:]  # 첫 번째 줄을 제외한 나머지
    line_height = bottom_font.getbbox("A")[3] + 3
    text_y = (image_height ) // 3

    # 색상 리스트: 번갈아 사용할 색상
    colors = ["#FFFFFF", "#FFFF00"]  # 흰색, 노란색

    for line in bottom_lines:
        line = line.strip()
        # 하단 줄을 분리하여 20자 이상일 경우 나눔
        split_lines = split_top_line(line, max_length=10)

        for i, sub_line in enumerate(split_lines):
            sub_line = sub_line.strip()
            text_width = bottom_font.getbbox(sub_line)[2]

            if alignment == "center":
                text_x = (image_width - text_width) // 2
            elif alignment == "left":
                text_x = 10
            elif alignment == "right":
                text_x = image_width - text_width - 10
            else:
                raise ValueError("Invalid alignment option. Choose 'center', 'left', or 'right'.")

            # 현재 줄 렌더링, 색상은 colors[i % len(colors)]로 선택
            draw.text((text_x, text_y), sub_line, font=bottom_font, fill=colors[i % len(colors)])
            text_y += line_height  # 다음 줄로 이동

    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_x = 10
    store_name_y = image_height - (image_height / 13) # 분모가 작을수록 하단에 더 멀게
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="white")
    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"




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