from fastapi import (
    APIRouter, UploadFile, File, Form, HTTPException, status
)
from app.schemas.ads import (
    AdsList, AdsInitInfoOutPut,
    AdsGenerateContentOutPut, AdsContentRequest,
    AdsGenerateImageOutPut, AdsImageRequest,
    AdsDeleteRequest, AdsContentNewRequest, AuthCallbackRequest,
    AdsTestRequest, AdsSuggestChannelRequest
)
from fastapi import Request, Body
from PIL import Image
import logging
from typing import List
from google_auth_oauthlib.flow import Flow

from app.service.ads import (
    select_ads_init_info as service_select_ads_init_info,
    insert_ads as service_insert_ads,
    delete_status as service_delete_status,
    update_ads as service_update_ads,
)
from app.service.ads_generate import (
    generate_content as service_generate_content,
    generate_image as service_generate_image,
    generate_video as service_generate_video,
    generate_new_content as service_generate_new_content,
    generate_old_content as service_generate_old_content,
    generate_claude_content as service_generate_claude_content,
    generate_image_mid as service_generate_image_mid
)
from app.service.ads_upload import (
    upload_story_ads as service_upload_story_ads,
    upload_feed_ads as service_upload_feed_ads,
    upload_mms_ads as service_upload_mms_ads,
    upload_youtube_ads as service_upload_youtube_ads,
    upload_get_auth_url as service_upload_get_auth_url,
    upload_insta_info_ads as service_upload_insta_info_ads
)
from app.service.ads_generate_by_title import (
    combine_ads_1_1 as service_combine_ads_1_1,
    combine_ads_4_7 as service_combine_ads_4_7,
    combine_ads_7_4 as service_combine_ads_7_4,
)
# from app.service.ads_upload_naver import upload_naver_ads as service_upload_naver_ads
import traceback
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
from typing import Optional
from dotenv import load_dotenv
from datetime import datetime
import os
import uuid
import json



router = APIRouter()
logger = logging.getLogger(__name__)

ROOT_PATH = Path(os.getenv("ROOT_PATH"))
IMAGE_DIR = Path(os.getenv("IMAGE_DIR"))
FULL_PATH = ROOT_PATH / IMAGE_DIR.relative_to("/") / "ads"
FULL_PATH.mkdir(parents=True, exist_ok=True)


# 매장 리스트에서 모달창 띄우기
@router.post("/select/init/info", response_model=AdsInitInfoOutPut)
def select_ads_init_info(store_business_number: str, request: Request):
    # 쿼리 매개변수로 전달된 store_business_number 값 수신
    try:
        # 요청 정보 출력
        # logger.info(f"Request received from {request.client.host}:{request.client.port}")
        # logger.info(f"Request headers: {request.headers}")
        # logger.info(f"Request path: {request.url.path}")
        return service_select_ads_init_info(store_business_number)
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 광고 채널 추천
@router.post("/suggest/channel")
def select_ads_init_info(request: AdsSuggestChannelRequest):
    # 쿼리 매개변수로 전달된 store_business_number 값 수신
    try:
        gpt_role = '''
            다음과 같은 매장에서 온라인 홍보 콘텐츠를 제작하여 포스팅하려고 합니다. 
            이 매장에서 가장 좋은 포스팅 채널은 무엇이 좋겠습니까? 
            제시된 채널 중에 하나를 선택해주고 그 이유와 홍보전략을 300자 내외로 작성해주세요.
        '''

        prompt = f'''
            매장명 : {request.store_name}
            주소 : {request.road_name}
            업종 : {request.tag}
            주 고객층 : {request.male_base}, {request.female_base}
            홍보 주제 : {request.title}
            온라인 홍보채널 : 문자메시지, 인스타그램 스토리, 인스타그램 피드, 네이버 블로그, 카카오톡, 자사 홈페이지, 페이스북, 디스코드, 트위터, 미디엄, 네이버 밴드, 캐치테이블, 배달의 민족
        '''

        detail_contet = "값 없음"

        channel = service_generate_content(
            prompt,
            gpt_role,
            detail_contet
        )
        return {"chan": channel}
    except Exception as e:
        print(f"Error occurred: {e}, 문구 생성 오류")


# 업로드 된 이미지 처리
@router.post("/generate/exist/image")
def generate_image_with_text(
    store_name: str = Form(...),
    road_name: str = Form(...),
    tag: str = Form(...),
    weather: str = Form(...),
    temp: float = Form(...),
    male_base: str = Form(...),
    female_base: str = Form(...),
    gpt_role: str = Form(...),
    detail_content: str = Form(...),
    use_option: str = Form(...),
    title: str = Form(...),
    image: UploadFile = File(...)
):
    images_list = []
    print(image)
    try:
        # 문구 생성
        try:
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')

            copyright_prompt = f'''
                매장명 : {store_name}
                주소 : {road_name}
                업종 : {tag}
                날짜 : {formattedToday}
                날씨 : {weather}, {temp}℃
                매출이 가장 높은 남성 연령대 : {male_base}
                매출이 가장 높은 여성 연령대 : {female_base}
            '''
            copyright = service_generate_content(
                copyright_prompt,
                gpt_role,
                detail_content
            )
            
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")

        # 이미지와 문구 합성
        try:
            pil_image = Image.open(image.file)
            image_width, image_height = pil_image.size

            if use_option == '인스타그램 피드':
                if title == '이벤트':
                    # 서비스 레이어 호출 (Base64 이미지 반환)
                    image1, image2 = service_combine_ads_1_1(store_name, road_name, copyright, title, image_width, image_height, pil_image)
                    images_list.extend([image1, image2])
                elif title == '매장 소개':
                    # 서비스 레이어 호출 (Base64 이미지 반환)
                    image1 = service_combine_ads_1_1(store_name, road_name, copyright, title, image_width, image_height, pil_image)
                    images_list.append(image1)
            elif use_option == '인스타그램 스토리' or use_option == '문자메시지':
                if title == '이벤트':
                    # 서비스 레이어 호출 (Base64 이미지 반환)
                    image1, image2 = service_combine_ads_4_7(store_name, road_name, copyright, title, image_width, image_height, pil_image)
                    images_list.extend([image1, image2])
                elif title == '매장 소개':
                    # 서비스 레이어 호출 (Base64 이미지 반환)
                    image1 = service_combine_ads_4_7(store_name, road_name, copyright, title, image_width, image_height, pil_image)
                    images_list.append(image1)

        except Exception as e:
            print(f"Error occurred: {e}, 이미지 합성 오류")
        # 문구와 합성된 이미지 반환
        return JSONResponse(content={"copyright": copyright, "images": images_list})

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# 테스트용
@router.post("/upload/content")
def generate_upload(request: AdsTestRequest):
    try:
        # 문구 생성
        try:
            today = datetime.now()
            formattedToday = today.strftime('%Y-%m-%d (%A) %H:%M')

            copyright_prompt = f'''
                매장명 : {request.store_name}
                주소 : {request.road_name}
                업종 : {request.tag}
                날짜 : {formattedToday}
                날씨 : {request.weather}, {request.temp}℃
                매출이 가장 높은 남성 연령대 : {request.male_base}
                매출이 가장 높은 여성 연령대 : {request.female_base}
            '''

            copyright = service_generate_content(
                copyright_prompt,
                request.gpt_role,
                request.detail_content
            )
        except Exception as e:
            print(f"Error occurred: {e}, 문구 생성 오류")
        
        # 스토리 생성
        try:
            korean_story_prompt = f"""
                - 세부업종 : {request.tag}
                - 날짜 : {formattedToday}
                - 날씨 : {request.weather}, {request.temp}℃
                - 매출이 가장 높은 남성 연령대 : {request.male_base}
                - 매출이 가장 높은 여성 연령대 : {request.female_base}
                - 장소 : {request.road_name}
                - 추가정보 내용 : {request.detail_content}
                - 홍보채널 : {request.use_option}
                - 홍보채널에 포스팅되는 이미지나 동영상의 특징을 살려서 매장의 특성과 브랜드를 잘 느낄 수 있을것. 
                - 주요고객이 오늘의 날씨와 환경, 날짜, 장소의 특징을 감안하여 매장에 대한 호감도를 느낄 수 있는 스토리를 작성할 것
                - 매장의 세부업종에 따른 이미지 컨셉을 도출하여 스토리에 접목시킬 것
            """
            korean_story_gpt_role = f'''
                우수한 마케터의 역할과 역량을 학습한 이후 아래와 같은 내용의 마케팅 스토리를 300자 내외로 작성해주세요.
            '''

            detail_content = "값 없음"

            korean_story = service_generate_content(
                korean_story_prompt,
                korean_story_gpt_role,
                detail_content
            )
        except Exception as e:
            print(f"Error occurred: {e}, 스토리 생성 오류")

        # 스토리를 바탕으로 한 이미지 프롬프트 생성
        try:
            korean_image_gpt_role = f'''
                - 이 스토리로 dalle AI를 통해 {request.use_option}에 업로드할 이미지를 생성하기 위한 프롬프트를 작성해주세요. 
                - 프롬프트를 작성할때 스토리에 어울리는 이미지 스타일, 구도, 방식, 50대 남성의 감성에 어울리는 이미지를 생성할 수 있도록 작성해주세요.

                이미지 스타일 사례
                - 3D 그래픽, 2D그래픽, 일러스트레이션, 페이퍼 크라프트, 일본 애니메이션, 만화책, 사진, 디오라마, 아이소메트릭, 광고포스터, 판타지, 타이포그라피 등
            '''

            detail_content = "값 없음"

            korean_image_prompt = service_generate_content(
                korean_story,
                korean_image_gpt_role,
                detail_content
            )
            print(korean_image_prompt)
        except Exception as e:
            print(f"Error occurred: {e}, 이미지 생성 오류")

        # 이미지 생성
        try:
            if request.ai_model_option == 'midJouney':
                origin_image = service_generate_image_mid(
                    request.use_option,
                    korean_image_prompt
                )
            else:
                origin_image = service_generate_image(
                    request.use_option,
                    korean_image_prompt
                )
        except Exception as e:
            print(f"Error occurred: {e}, 이미지 생성 오류")

        # 사이즈 조정 및 합성
        images_list = []
        try:
            for i, img in enumerate(origin_image):
                image_width, image_height = img.size  # 이미지 크기 가져오기
                print(f"Image {i + 1}: Width = {image_width}, Height = {image_height}")

                if request.use_option == '인스타그램 피드':
                    if request.title == '이벤트':
                        # 서비스 레이어 호출 (Base64 이미지 반환)
                        image1, image2 = service_combine_ads_1_1(request.store_name, request.road_name, copyright, request.title, image_width, image_height, img)
                        images_list.extend([image1, image2])
                    elif request.title == '매장 소개':
                        # 서비스 레이어 호출 (Base64 이미지 반환)
                        image1 = service_combine_ads_1_1(request.store_name, request.road_name, copyright, request.title, image_width, image_height, img)
                        images_list.append(image1)
                elif request.use_option == '인스타그램 스토리' or request.use_option == '문자메시지':
                    if request.title == '이벤트':
                        # 서비스 레이어 호출 (Base64 이미지 반환)
                        image1, image2 = service_combine_ads_4_7(request.store_name, request.road_name, copyright, request.title, image_width, image_height, img)
                        images_list.extend([image1, image2])
                    elif request.title == '매장 소개':
                        # 서비스 레이어 호출 (Base64 이미지 반환)
                        image1 = service_combine_ads_4_7(request.store_name, request.road_name, copyright, request.title, image_width, image_height, img)
                        images_list.append(image1)
        except Exception as e:
            print(f"Error occurred: {e}, 이미지 합성 오류")
        
        # 문구와 합성된 이미지 반환
        return JSONResponse(content={"copyright": copyright, "images": images_list})

    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


# 문구 생성
@router.post("/generate/content", response_model=AdsGenerateContentOutPut)
def generate_content(request: AdsContentRequest):
    try:
        # print('깃허브 푸시용 테스트')
        # 서비스 레이어 호출: 요청의 데이터 필드를 unpack
        data = service_generate_content(
            request.prompt,
            request.gpt_role,
            request.detail_content
        )
        return {"content": data}  
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


# 모달창에서 이미지 생성하기
@router.post("/generate/image", response_model=AdsGenerateImageOutPut)
def generate_image(request: AdsImageRequest):
    try:
        # print(request.ai_model_option)
        if request.ai_model_option == 'midJouney':
            data = service_generate_image_mid(
                request.use_option,
                request.ai_mid_prompt,
            )
            return data
        else:
            # 서비스 레이어 호출: 요청의 데이터 필드를 unpack
            data = service_generate_image(
                request.use_option,
                request.ai_model_option,
                request.ai_prompt,
            )
            return data
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        print(f"HTTPException 발생: {http_ex.detail}")  # 추가 디버깅 출력
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        print(f"Exception 발생: {error_msg}")  # 추가 디버깅 출력
        raise HTTPException(status_code=500, detail=error_msg)

# ADS 텍스트, 이미지 합성
@router.post("/combine/image/text")
def combine_ads(
    store_name: str = Form(...),
    road_name: str = Form(...),
    content: str = Form(...),
    use_option: str = Form(...),
    title: str = Form(...),
    image_width: int = Form(...),
    image_height: int = Form(...),
    image: UploadFile = File(...)
):
    try:
        pil_image = Image.open(image.file)
    except Exception as e:
        return {"error": f"Failed to open image: {str(e)}"}
    
    if use_option == '인스타그램 피드':
        if title == '이벤트':
            # 서비스 레이어 호출 (Base64 이미지 반환)
            image1, image2 = service_combine_ads_1_1(store_name, road_name, content, title, image_width, image_height, pil_image)
            return JSONResponse(content={"images": [image1, image2]})
        elif title == '매장 소개':
            # 서비스 레이어 호출 (Base64 이미지 반환)
            image1 = service_combine_ads_1_1(store_name, road_name, content, title, image_width, image_height, pil_image)
            return JSONResponse(content={"images": [image1]})
    elif use_option == '인스타그램 스토리' or use_option == '문자메시지':
        if title == '이벤트':
            # 서비스 레이어 호출 (Base64 이미지 반환)
            image1, image2 = service_combine_ads_4_7(store_name, road_name, content, title, image_width, image_height, pil_image)
            return JSONResponse(content={"images": [image1, image2]})
        elif title == '매장 소개':
            # 서비스 레이어 호출 (Base64 이미지 반환)
            image1 = service_combine_ads_4_7(store_name, road_name, content, title, image_width, image_height, pil_image)
            return JSONResponse(content={"images": [image1]})



# # ADS 텍스트, 이미지 합성
# @router.post("/combine/image/text")
# def combine_ads(
#     store_name: str = Form(...),
#     road_name: str = Form(...),
#     content: str = Form(...),
#     image_width: int = Form(...),
#     image_height: int = Form(...),
#     image: UploadFile = File(...)
# ):
#     try:
#         pil_image = Image.open(image.file)
#     except Exception as e:
#         return {"error": f"Failed to open image: {str(e)}"}
#     # 서비스 레이어 호출 (Base64 이미지 반환)
#     base64_image = service_combine_ads_ver1(store_name, road_name, content, image_width, image_height, pil_image)

#     # JSON 응답으로 Base64 이미지 반환
#     return JSONResponse(content={"image": base64_image})


# ADS DB에 저장
@router.post("/insert")
def insert_ads(
    store_business_number: str = Form(...),
    use_option: str = Form(...),
    title: str = Form(...),
    detail_title: Optional[str] = Form(None),  # 선택적 필드
    content: str = Form(...),
    image: UploadFile = File(None),
    final_image: UploadFile = File(None)  # 단일 이미지 파일
):
    # 이미지 파일 처리
    image_url = None
    if image:
        try:
            # 고유 이미지 명 생성
            filename, ext = os.path.splitext(image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_{today}_{uuid.uuid4()}{ext}"

            # 파일 저장 경로 지정
            file_path = os.path.join(FULL_PATH, unique_filename)

            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

            # 이미지 URL 생성
            image_url = f"/static/images/ads/{unique_filename}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving image file: {str(e)}"
            )

    # 파이널 이미지 파일 처리
    final_image_url = None
    if final_image:
        try:
            # 고유 이미지 명 생성
            filename, ext = os.path.splitext(final_image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_final_{today}_{uuid.uuid4()}{ext}"

            # 파일 저장 경로 지정
            file_path = os.path.join(FULL_PATH, unique_filename)

            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(final_image.file, buffer)

            # 파이널 이미지 URL 생성
            final_image_url = f"/static/images/ads/{unique_filename}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving final_image file: {str(e)}"
            )

    # 데이터 저장 호출
    try:
        ads_pk = service_insert_ads(
            store_business_number, 
            use_option, 
            title, 
            detail_title, 
            content, 
            image_url, 
            final_image_url
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inserting ad data: {str(e)}"
        )

    # 성공 응답 반환
    return ads_pk

# ADS 삭제처리
@router.post("/delete/status")
def delete_status(request: AdsDeleteRequest):
    try:
        # 서비스 레이어를 통해 업데이트 작업 수행
        success = service_delete_status(
            request.ads_id,
        )
        if success:
            return success
    except Exception as e:
        # 예외 처리
        print(f"Error occurred: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    


# ADS DB에 수정
@router.post("/update")
def update_ads(
    store_business_number: str = Form(...),
    use_option: str = Form(...),
    title: str = Form(...),
    detail_title: Optional[str] = Form(None),  # 선택적 필드
    content: str = Form(...),
    image: UploadFile = File(None),
    final_image: UploadFile = File(None)  # 단일 이미지 파일
):
    
    # 이미지 파일 처리
    image_url = None
    if image:
        try:
            # 고유 이미지 명 생성
            filename, ext = os.path.splitext(image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_{today}_{uuid.uuid4()}{ext}"

            # 파일 저장 경로 지정
            file_path = os.path.join(FULL_PATH, unique_filename)

            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

            # 이미지 URL 생성
            image_url = f"/static/images/ads/{unique_filename}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving image file: {str(e)}"
            )

    # 파이널 이미지 파일 처리
    final_image_url = None
    if final_image:
        try:
            # 고유 이미지 명 생성
            filename, ext = os.path.splitext(final_image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_final_{today}_{uuid.uuid4()}{ext}"

            # 파일 저장 경로 지정
            file_path = os.path.join(FULL_PATH, unique_filename)

            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(final_image.file, buffer)

            # 파이널 이미지 URL 생성
            final_image_url = f"/static/images/ads/{unique_filename}"
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving final_image file: {str(e)}"
            )

    # 데이터 저장 호출
    try:
        service_update_ads(
            store_business_number, 
            use_option, 
            title, 
            detail_title, 
            content, 
            image_url, 
            final_image_url
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating ad data: {str(e)}"
        )

    # 성공 응답 반환
    return {
        "store_business_number": store_business_number,
        "use_option": use_option,
        "title": title,
        "detail_title": detail_title,
        "content": content,
        "image_url": image_url,
        "final_image_url": final_image_url
    }


# 업로드
@router.post("/upload")
async def upload_ads(
    use_option: str = Form(...), 
    content: str = Form(...), 
    store_name: str = Form(...), 
    tag: str = Form(...), 
    upload_image: UploadFile = File(None),
):
    """
    광고 업로드 엔드포인트
    """
    final_image_url = None
    # print(access_token)
    # 1. 파이널 이미지 파일 처리
    if upload_image:
        try:
            filename, ext = os.path.splitext(upload_image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_final_{today}_{uuid.uuid4()}{ext}"
            file_path = os.path.join(FULL_PATH, unique_filename)

            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(upload_image.file, buffer)

            # 파이널 이미지 URL 생성
            final_image_url = f"/static/images/ads/{unique_filename}"
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": f"Error saving final_image file: {str(e)}",
                    "traceback": traceback.format_exc()
                }
            )

    # # 2. 유튜브 썸네일 처리
    # if use_option == "유튜브 썸네일":
    #     # 토큰이 없는 경우 인증 URL 반환
    #     if not access_token:
    #         state = json.dumps({
    #             "content": content,
    #             "store_name": store_name,
    #             "tag": tag,
    #             "file_path": file_path,
    #         })

    #         auth_url = service_upload_get_auth_url(state=state)
    #         return {"auth_url": auth_url["auth_url"]}

    # 3. 다른 업로드 옵션 처리
    try:
        if use_option == "인스타그램 스토리":
            insta_name, user_id, follower_count, media_count = service_upload_insta_info_ads()
            service_upload_story_ads(content, file_path)
            return insta_name, follower_count, media_count
        elif use_option == "인스타그램 피드":
            user_id, follower_count, media_count = service_upload_insta_info_ads()
            service_upload_feed_ads(content, file_path)
            return user_id, follower_count, media_count
        elif use_option == "문자메시지":
            await service_upload_mms_ads(content, file_path)
        elif use_option == '유튜브 썸네일':
            service_upload_youtube_ads(content, store_name, tag, file_path)
        # elif use_option == '네이버 블로그':
        #     service_upload_naver_ads(content, store_name, tag, file_path)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": f"Error processing ad data: {str(e)}",
                "traceback": traceback.format_exc()
            }
        )

    # 4. 성공 응답 반환
    return {
        "content": content,
        "final_image_url": final_image_url
    }


ROOT_PATH = os.getenv("ROOT_PATH")
AUTH_PATH = os.getenv("AUTH_PATH")

@router.post("/auth/callback")
def youtube_auth_callback(request: AuthCallbackRequest):
    CLIENT_SECRETS_FILE = os.path.join(ROOT_PATH, AUTH_PATH.lstrip("/"), "google_auth_wiz.json")
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    REDIRECT_URI = "http://localhost:3002/ads/auth/callback"

    code = request.code
    try:
        # Google OAuth Flow 초기화
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            SCOPES,
            redirect_uri=REDIRECT_URI,
        )

        # 인증 코드로 액세스 토큰 교환
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # 반환된 액세스 토큰
        access_token = credentials.token
        return {"access_token": access_token}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": f"Error exchanging auth code: {str(e)}"},
        )



# 유튜브 업로드 영상
@router.post("/upload/youtube")
async def upload_youtube_ads(
    content: str = Form(...), 
    store_name: str = Form(...), 
    tag: str = Form(...), 
    file_path: str = Form(None),
    access_token: str = Form(None),
):
    try:
        response = service_upload_youtube_ads(content, store_name, tag, file_path, access_token)
        return {"youtube_response": response}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"Error uploading to YouTube: {str(e)}"},
        )




# Ads 영상 만들기
@router.post("/generate/video")
def generate_video(
    title: str = Form(...),
    final_image: UploadFile = File(None)  # 단일 이미지 파일
):
    
    # 파이널 이미지 파일 처리
    if final_image:
        try:
            # 고유 이미지 명 생성
            filename, ext = os.path.splitext(final_image.filename)
            today = datetime.now().strftime("%Y%m%d")
            unique_filename = f"{filename}_jyes_ads_final_{today}_{uuid.uuid4()}{ext}"
            file_path = os.path.join(FULL_PATH, unique_filename)
            # 파일 저장
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(final_image.file, buffer)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving final_image file: {str(e)}"
            )
    
    # 데이터 저장 호출
    try:
        result_url= service_generate_video(file_path)
        return {"result_url" : result_url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inserting ad data: {str(e)}"
        )


# 새 모델 테스트
@router.post("/generate/test/new/content", response_model=AdsGenerateContentOutPut)
def generate_new_content(request: AdsContentNewRequest):
    try:
        # print(request.prompt)
        # 서비스 레이어 호출: 요청의 데이터 필드를 unpack
        content = service_generate_new_content(
            request.prompt
        )
        return {'content': content}
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 구 모델 테스트
@router.post("/generate/test/old/content", response_model=AdsGenerateContentOutPut)
def generate_old_content(request: AdsContentNewRequest):
    try:
        # print(request.prompt)
        # 서비스 레이어 호출: 요청의 데이터 필드를 unpack
        content = service_generate_old_content(
            request.prompt
        )
        return {'content': content}
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

# 클로드 모델 테스트
@router.post("/generate/test/claude/content", response_model=AdsGenerateContentOutPut)
def generate_claude_content(request: AdsContentNewRequest):
    try:
        # print(request.prompt)
        # 서비스 레이어 호출: 요청의 데이터 필드를 unpack
        content = service_generate_claude_content(
            request.prompt
        )
        return {'content': content}
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)