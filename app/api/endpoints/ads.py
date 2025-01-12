from fastapi import (
    APIRouter, UploadFile, File, Form, HTTPException, status
)
from app.schemas.ads import (
    AdsList, AdsInitInfoOutPut,
    AdsGenerateContentOutPut, AdsContentRequest,
    AdsGenerateImageOutPut, AdsImageRequest,
    AdsDeleteRequest, AdsContentNewRequest
)
from fastapi import Request
from PIL import Image
import logging
from typing import List
from app.service.ads import (
    select_ads_init_info as service_select_ads_init_info,
    insert_ads as service_insert_ads,
    delete_status as service_delete_status,
    update_ads as service_update_ads,
    select_ads_specific_info as service_select_ads_specific_info
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
)
from app.service.ads_generate_by_title import combine_ads as service_combine_ads
# from app.service.ads_upload_naver import upload_naver_ads as service_upload_naver_ads
import traceback
from fastapi.responses import JSONResponse
from pathlib import Path
from fastapi.responses import JSONResponse
import shutil
from typing import Optional
from dotenv import load_dotenv
from datetime import datetime
import os
import uuid
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
    
    

# 모달창에서 문구 생성하기
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
    
    if use_option == '인스타 피드':
        # 서비스 레이어 호출 (Base64 이미지 반환)
        image = service_combine_ads(store_name, road_name, content, title, image_width, image_height, pil_image)
    
    else :
        image = service_combine_ads(store_name, road_name, content, title, image_width, image_height, pil_image)

    # JSON 응답으로 두 이미지를 반환
    return JSONResponse(content={"images": [image]})

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
async def upload_ads(use_option: str = Form(...), content: str = Form(...), store_name: str = Form(...), tag: str = Form(...), upload_image: UploadFile = File(None)):
    """
    광고 업로드 엔드포인트
    """
    final_image_url = None

    # 파이널 이미지 파일 처리
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
            error_trace = traceback.format_exc()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": f"Error saving final_image file: {str(e)}",
                    "traceback": error_trace
                }
            )

    # 데이터 저장 호출
    try:
        if use_option == '인스타그램 스토리':
            service_upload_story_ads(content, file_path)
        elif use_option == '인스타그램 피드':
            service_upload_feed_ads(content, file_path)
        elif use_option == '문자메시지':
            await service_upload_mms_ads(content, file_path)
        elif use_option == '유튜브 썸네일':
            service_upload_youtube_ads(content, store_name, tag, file_path)
        # elif use_option == '네이버 블로그':
        #     service_upload_naver_ads(content, store_name, tag, file_path)
    except Exception as e:
        error_trace = traceback.format_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": f"Error inserting ad data: {str(e)}",
                "traceback": error_trace
            }
        )

    # 성공 응답 반환
    return {
        "content": content,
        "final_image_url": final_image_url
    }



# Ads 카톡 홍보용 url 만들기
@router.post("/promote/detail")
def select_ads_specific_info(ads_id: int):
    try:
        # 요청 정보 출력
        # logger.info(f"Request received from {request.client.host}:{request.client.port}")
        # logger.info(f"Request headers: {request.headers}")
        # logger.info(f"Request path: {request.url.path}")
        data = service_select_ads_specific_info(ads_id)
        return data
    except HTTPException as http_ex:
        logger.error(f"HTTP error occurred: {http_ex.detail}")
        raise http_ex
    except Exception as e:
        error_msg = f"Unexpected error while processing request: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
    

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