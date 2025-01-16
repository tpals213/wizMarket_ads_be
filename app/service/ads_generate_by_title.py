import os
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO
import base64
import re
from moviepy import *



def combine_ads_1_1 (store_name, road_name, content, title, image_width, image_height, image):
    if title == "매장 소개":
        image = combine_ads_store_intro(store_name, road_name, content, image_width, image_height, image, alignment="center")
        return image
    elif title == "이벤트":
        image1 = combine_ads_event(store_name, road_name, content, image_width, image_height, image, alignment="center")
        image2 = combine_ads_event_ver2(store_name, road_name, content, image_width, image_height, image, alignment="center")
        return image1, image2
    

def combine_ads_4_7 (store_name, road_name, content, title, image_width, image_height, image):
    if title == "매장 소개":
        image = combine_ads_event_4_7(store_name, road_name, content, image_width, image_height, image)
        return image
    elif title == "이벤트":
        image1 = combine_ads_event_4_7(store_name, road_name, content, image_width, image_height, image)
        return image1
    

def combine_ads_7_4 (store_name, road_name, content, title, image_width, image_height, image):
    if title == "매장 소개":
        image = combine_ads_store_intro(store_name, road_name, content, image_width, image_height, image, alignment="center")
        return image
    elif title == "이벤트":
        image1 = combine_ads_event(store_name, road_name, content, image_width, image_height, image, alignment="center")
        return image1


# 텍스트 자르기
def split_top_line(text, max_length):

    result = []
    words = text.strip().split()
    # print(words)
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


# 이미지 사이즈 조정
def resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1024):
    # 1. 가로 세로 모두 want_width와 want_height보다 작은 경우
    if image_width < want_width and image_height < want_height:
        image = image.resize((want_width, want_height), Image.Resampling.LANCZOS)
        image_width, image_height = want_width, want_height

    # 2. 가로나 세로 둘 중 하나만 작은 경우
    elif image_width < want_width or image_height < want_height:
        if image_width < want_width:  # 가로가 작을 경우
            scale_factor = want_width / image_width
            new_height = int(image_height * scale_factor)
            image = image.resize((want_width, new_height), Image.Resampling.LANCZOS)
            image_width, image_height = want_width, new_height
        else:  # 세로가 작을 경우
            scale_factor = want_height / image_height
            new_width = int(image_width * scale_factor)
            image = image.resize((new_width, want_height), Image.Resampling.LANCZOS)
            image_width, image_height = new_width, want_height

        # 큰 쪽 잘라내기
        if image_width > want_width:  # 가로가 want_width를 넘으면 자름
            left = (image_width - want_width) // 2
            image = image.crop((left, 0, left + want_width, want_height))
            image_width, image_height = want_width, want_height
        elif image_height > want_height:  # 세로가 want_height를 넘으면 자름
            top = (image_height - want_height) // 2
            image = image.crop((0, top, want_width, top + want_height))
            image_width, image_height = want_width, want_height

    # 3. 가로나 세로 둘 중 하나만 큰 경우
    elif image_width > want_width or image_height > want_height:
        if image_width > want_width and image_height <= want_height:  # 가로만 큰 경우
            left = (image_width - want_width) // 2
            image = image.crop((left, 0, left + want_width, image_height))
            image_width = want_width
        elif image_height > want_height and image_width <= want_width:  # 세로만 큰 경우
            top = (image_height - want_height) // 2
            image = image.crop((0, top, image_width, top + want_height))
            image_height = want_height

    # 4. 가로 세로 모두 want_width와 want_height보다 큰 경우
    elif image_width > want_width and image_height > want_height:
        left = (image_width - want_width) // 2
        top = (image_height - want_height) // 2
        image = image.crop((left, top, left + want_width, top + want_height))
        image_width, image_height = want_width, want_height

    return want_width, want_height, image


    
# 주제 + 문구 + 이미지 합치기
def combine_ads_store_intro(store_name, road_name, content, image_width, image_height, image, alignment="center"):
    root_path = os.getenv("ROOT_PATH", ".")
    sp_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "BG_snow.png") 
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1024)
  
    # 바탕 생성 및 합성
    rectangle_path = os.path.join(root_path, "app", "static", "images", "ads_back", "introduction_back.png") 
    rectangle = Image.open(rectangle_path).convert("RGBA")
    rectangle = rectangle.resize(image.size)
    image = Image.alpha_composite(image, rectangle)

    # sp_image 불러오기 및 리사이즈
    sp_image = Image.open(sp_image_path).convert("RGBA")
    original_width, original_height = sp_image.size

    # sp_image의 가로 길이를 기존 이미지의 가로 길이에 맞추고, 세로는 비율에 맞게 조정
    new_width = image_width
    new_height = int((new_width / original_width) * original_height)
    sp_image = sp_image.resize((new_width, new_height))
    # 투명도 조정
    alpha = sp_image.split()[3]  # RGBA의 알파 채널 추출
    alpha = ImageEnhance.Brightness(alpha).enhance(0.5)  # 투명도를 0.6으로 조정
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
    top_path = os.path.join(root_path, "app", "static", "font", "GasoekOne-Regular.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "BMHANNA_11yrs_ttf.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-Bold.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    top_font_size = 150
    bottom_font_size = (top_font_size * 5) / 8
    store_name_font_size = 64
    road_name_font_size = 48

    # 폰트 설정
    top_font = ImageFont.truetype(top_path, int(top_font_size))
    bottom_font = ImageFont.truetype(bottom_path, int(bottom_font_size))
    store_name_font = ImageFont.truetype(store_name_path, int(store_name_font_size))
    road_name_font = ImageFont.truetype(road_name_path, int(road_name_font_size))

    # 텍스트 렌더링 (합성 작업 후)
    draw = ImageDraw.Draw(image)

    content = content.strip('"')
    lines = content
    # print(content)
    if len(lines) > 0:
        top_line = lines
        lines_list = split_top_line(top_line, max_length=9)  # 반환값은 리스트
        
        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 270
        
        # 반복적으로 각 줄 렌더링
        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비 계산
                top_text_width = top_font.getbbox(line)[2]
                
                # 좌우 여백을 고려한 중앙 정렬 X 좌표 계산
                top_text_x = (image_width - 44 - 44 - top_text_width) // 2 + 44
                
                # 현재 줄 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill=(163, 163, 163, 178))  # RGBA 적용
                
                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5


    
    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_height = store_name_font.getbbox(store_name)[3]
    store_name_x = (image_width - store_name_width) // 2
    store_name_y = image_height - store_name_height - 106
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="#0BE855")

    # road_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_height = road_name_font.getbbox(road_name)[3]
    road_name_x = (image_width - road_name_width) // 2
    road_name_y = image_height - road_name_height - 23
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill=(255, 255, 255))


    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"


def combine_ads_event(store_name, road_name, content, image_width, image_height, image, alignment="center"):
    # print(image_width, image_height)
    root_path = os.getenv("ROOT_PATH", ".")
    
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1024)

    # 바탕 생성 및 합성
    rectangle_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_1_1.png")
    rectangle = Image.open(rectangle_path).convert("RGBA")
    
    # 새로운 이미지 크기 계산
    new_height = max(image_height, rectangle.height)  # 기존 높이와 추가 높이 중 더 큰 값
    combined_background = Image.new("RGBA", (image_width, new_height), (0, 0, 0, 0))  # 투명 배경 생성
    
    # 기존 rectangle 이미지 복사
    combined_background.paste(rectangle, (0, 0))  # 상단에 원본 rectangle 붙이기
    
    # 원본 이미지와 새 배경 합성
    image = Image.alpha_composite(image, combined_background)


    sp_image_path = os.path.join(root_path, "app", "static", "images", "ads_back", "new_imo.png") 

    # sp_image 불러오기 및 리사이즈
    sp_image = Image.open(sp_image_path).convert("RGBA")
    original_width, original_height = sp_image.size

    # sp_image의 가로 길이를 기존 이미지의 가로 길이의 1/4로 맞추고, 세로는 비율에 맞게 조정
    new_width = 234
    new_height = 234
    sp_image = sp_image.resize((new_width, new_height))

    # 4번 위치 (하단 오른쪽) 중심 좌표 계산
    offset_x = (image_width * 3 // 4) - (new_width // 2)  # 4등분 했을 때 하단 오른쪽 중심 X
    offset_y = (image_height * 3 // 4) - (new_height // 2)  # 4등분 했을 때 하단 오른쪽 중심 Y

    # sp_image를 기존 이미지 위에 합성 (투명도 제거)
    image.paste(sp_image, (offset_x, offset_y), sp_image)

    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "JalnanGothicTTF.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    top_font_size = 55
    bottom_font_size = 96
    store_name_font_size = 64
    road_name_font_size = 48

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
    # lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
    # lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    lines = re.findall(r':\s*(.*)', content)  # ':' 이후의 텍스트만 추출
    lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    # print(lines)

    if len(lines) > 0:
        top_line = lines[0].strip()
        lines_list = split_top_line(top_line, max_length=20)  # 반환값은 리스트

        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 100
        line_padding = 34  # 텍스트와 선 사이의 패딩

        # 반복적으로 각 줄 렌더링
        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비 계산
                top_text_width = top_font.getbbox(line)[2]
                top_text_height = top_font.getbbox(line)[3]  # 텍스트 높이 계산
                # 중앙 정렬 X 좌표 계산
                top_text_x = (image_width - 44 - 44 - top_text_width) // 2 + 44

                # 텍스트 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill=(255, 255, 255))

                # 첫 번째 줄에 윗줄 추가
                if i == 0:
                    line_start_x = top_text_x
                    line_end_x = top_text_x + top_text_width
                    draw.line(
                        [(line_start_x, top_text_y - line_padding),
                        (line_end_x, top_text_y - line_padding)],
                        fill=(255, 255, 255),
                        width=1
                    )

                # 마지막 줄에 밑줄 추가
                if i == len(lines_list) - 1:
                    line_start_x = top_text_x
                    line_end_x = top_text_x + top_text_width
                    draw.line(
                        [(line_start_x, top_text_y + top_text_height + line_padding),
                        (line_end_x, top_text_y + top_text_height + line_padding)],
                        fill=(255, 255, 255),
                        width=1
                    )

                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5

    # 하단 텍스트 추가
    bottom_lines = lines[1:]  # 첫 번째 줄을 제외한 나머지
    line_height = bottom_font.getbbox("A")[3] + 4
    text_y = 224

    for line in bottom_lines:
        line = line.strip()
        # 하단 줄을 분리하여 20자 이상일 경우 나눔
        split_lines = split_top_line(line, max_length=12)

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
            draw.text((text_x, text_y), sub_line, font=bottom_font, fill="#FFFB00")
            text_y += line_height  # 다음 줄로 이동

    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_height = store_name_font.getbbox(store_name)[3]
    store_name_x = (image_width - store_name_width) // 2
    store_name_y = image_height - store_name_height - 99
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="white")

    fill_color = (255, 255, 255, int(255 * 0.8))  # RGBA

    # road_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_height = road_name_font.getbbox(road_name)[3]
    road_name_x = (image_width - road_name_width) // 2
    road_name_y = image_height - road_name_height - 23
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill=fill_color)


    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"




def combine_ads_event_ver2(store_name, road_name, content, image_width, image_height, image, alignment="center"):
    # print(image_width, image_height)
    root_path = os.getenv("ROOT_PATH", ".")
    # print(image)
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1024)

    # 바탕 생성 및 합성
    rectangle_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_event_1_1.png")
    rectangle = Image.open(rectangle_path).convert("RGBA")
    
    # 새로운 이미지 크기 계산
    new_height = max(image_height, rectangle.height)  # 기존 높이와 추가 높이 중 더 큰 값
    combined_background = Image.new("RGBA", (image_width, new_height), (0, 0, 0, 0))  # 투명 배경 생성
    
    # 기존 rectangle 이미지 복사
    combined_background.paste(rectangle, (0, 0))  # 상단에 원본 rectangle 붙이기
    
    # 원본 이미지와 새 배경 합성
    image = Image.alpha_composite(image, combined_background)

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1024)

    # 투명 배경 생성 (1024x772 상단 투명)
    transparent_background = Image.new("RGBA", (image_width, 772), (0, 0, 0, 0))

    # 주황색 배경 생성 (1024x252 하단 주황색)
    orange_background = Image.new("RGBA", (image_width, 252), (255, 135, 6, int(0.5 * 255)))  # 투명도 50%

    # 전체 배경 합성 (1024x1024)
    combined_background = Image.new("RGBA", (image_width, image_height), (0, 0, 0, 0))  # 전체 배경
    combined_background.paste(transparent_background, (0, 0))  # 상단 투명 배경 추가
    combined_background.paste(orange_background, (0, 772))  # 하단 주황색 배경 추가

    # 기존 이미지와 배경 합성
    image = Image.alpha_composite(image, combined_background)

    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "SeoulNamsanB.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    top_font_size = 80
    bottom_font_size = 90
    store_name_font_size = 64
    road_name_font_size = 48

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
    # lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
    # lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    lines = re.findall(r':\s*(.*)', content)  # ':' 이후의 텍스트만 추출
    lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    # print(lines)

    if len(lines) > 0:
        top_line = lines[0].strip()
        lines_list = split_top_line(top_line, max_length=20)  # 반환값은 리스트

        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 93

        # 반복적으로 각 줄 렌더링
        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 텍스트 너비 계산
                top_text_width = top_font.getbbox(line)[2]
                top_text_height = top_font.getbbox(line)[3]  # 텍스트 높이 계산
                # 중앙 정렬 X 좌표 계산
                top_text_x = (image_width - 44 - 44 - top_text_width) // 2 + 44
                # 텍스트 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill=(255, 255, 255, 10))
                print(line)
                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5

    # 하단 텍스트 추가
    bottom_lines = lines[1:]  # 첫 번째 줄을 제외한 나머지
    line_height = bottom_font.getbbox("A")[3] + 4
    text_y = 379

    for line in bottom_lines:
        line = line.strip()
        # 하단 줄을 분리하여 20자 이상일 경우 나눔
        split_lines = split_top_line(line, max_length=12)

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

            draw.text((text_x, text_y), sub_line, font=bottom_font, fill="#FFFFFF")
            text_y += line_height  # 다음 줄로 이동

    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_x = (image_width - store_name_width) // 2
    store_name_y = 849
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="white")

    fill_color = (255, 255, 255, int(255 * 0.8))  # RGBA

    # road_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_x = (image_width - road_name_width) // 2
    road_name_y = 925
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill=fill_color)


    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"


def combine_ads_event_4_7(store_name, road_name, content, image_width, image_height, image):
    # print(image_width, image_height)
    root_path = os.getenv("ROOT_PATH", ".")
    # print(image)
    # RGBA 모드로 변환
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    # 이미지 크기 확인 및 리사이즈
    image_width, image_height, image = resize_and_crop_image(image_width, image_height, image, want_width=1024, want_height=1792)

    # 바탕 생성 및 합성
    rectangle_path = os.path.join(root_path, "app", "static", "images", "ads_back", "ads_back_intro_4_7.png")
    rectangle = Image.open(rectangle_path).convert("RGBA")
    
    # Rectangle 이미지 크기 확인
    rectangle_width, rectangle_height = rectangle.size

    # 투명 배경 생성: 이미지2 하단에 추가 (전체 높이 1792로 맞춤)
    transparent_height = image_height - rectangle_height
    transparent_background = Image.new("RGBA", (rectangle_width, transparent_height), (0, 0, 0, 0))  # 투명 배경 생성

    # Rectangle과 투명 배경 합성
    combined_rectangle = Image.new("RGBA", (rectangle_width, image_height), (0, 0, 0, 0))  # 전체 크기: 1024x1792
    combined_rectangle.paste(rectangle, (0, 0))  # Rectangle 상단 배치
    combined_rectangle.paste(transparent_background, (0, rectangle_height))  # 투명 배경 하단 배치

    # 이미지1(image)와 Rectangle 합성
    image = Image.alpha_composite(image, combined_rectangle)

    # 텍스트 설정
    top_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    bottom_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    store_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    road_name_path = os.path.join(root_path, "app", "static", "font", "Pretendard-R.ttf") 
    top_font_size = 110
    bottom_font_size = 80
    store_name_font_size = 48
    road_name_font_size = 48

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
    # lines = re.findall(r'[^.!?,\n]+[.!?,]?', content)
    # lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    lines = re.findall(r':\s*(.*)', content)  # ':' 이후의 텍스트만 추출
    lines = [line.strip() for line in lines if line.strip()]  # 공백 제거 및 빈 문자열 제외

    # print(lines)

    if len(lines) > 0:
        top_line = lines[0].strip()
        lines_list = split_top_line(top_line, max_length=8)  # 반환값은 리스트

        # 첫 번째 줄 렌더링 Y 좌표 설정
        top_text_y = 147

        # 반복적으로 각 줄 렌더링
        for i, line in enumerate(lines_list):
            if line:  # 줄이 존재할 경우만 처리
                # 중앙 정렬 X 좌표 계산
                top_text_x = 76
                # 텍스트 렌더링
                draw.text((top_text_x, top_text_y), line, font=top_font, fill=(255, 255, 255, 10))
                # print(line)
                # Y 좌표를 다음 줄로 이동
                top_text_y += top_font.getbbox("A")[3] + 5

    # 하단 텍스트 추가
    bottom_lines = lines[1:]  # 첫 번째 줄을 제외한 나머지
    line_height = bottom_font.getbbox("A")[3] + 4
    text_y = 484

    for line in bottom_lines:
        line = line.strip()
        # 하단 줄을 분리하여 20자 이상일 경우 나눔
        split_lines = split_top_line(line, max_length=12)

        for i, sub_line in enumerate(split_lines):
            sub_line = sub_line.strip()
            text_width = bottom_font.getbbox(sub_line)[2]

            text_x = 84

            draw.text((text_x, text_y), sub_line, font=bottom_font, fill="#FFFFFF")
            text_y += line_height  # 다음 줄로 이동

    # store_name 추가
    store_name_width = store_name_font.getbbox(store_name)[2]
    store_name_x = (image_width - store_name_width) // 2
    store_name_y = 1563
    draw.text((store_name_x, store_name_y), store_name, font=store_name_font, fill="white")

    fill_color = (255, 255, 255, int(255 * 0.8))  # RGBA

    # road_name 추가
    road_name_width = road_name_font.getbbox(road_name)[2]
    road_name_x = (image_width - road_name_width) // 2
    road_name_y = 1639
    draw.text((road_name_x, road_name_y), road_name, font=road_name_font, fill=fill_color)


    # 이미지 메모리에 저장
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    # Base64 인코딩
    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{base64_image}"