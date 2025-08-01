"""
단순화된 설정 파일 - S3와 파일 업로드 관련 기능만 유지
"""

import os
import boto3
import dotenv

dotenv.load_dotenv(override=True)

RESOURCE_BUCKET_NAME = os.getenv('RESOURCE_BUCKET_NAME')

# 환경 변수 검증
if not RESOURCE_BUCKET_NAME:
    raise ValueError("RESOURCE_BUCKET_NAME 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

try:
    s3_client = boto3.client('s3')
except Exception as e:
    raise ValueError(f"AWS S3 클라이언트 초기화 실패: {str(e)}")

# S3 스토리지 객체 반환 함수
def get_storage():
    """S3 스토리지 객체 반환"""
    from src.uploads.s3_storage import S3Storage
    return S3Storage(
        bucket_name=RESOURCE_BUCKET_NAME,
        s3_client=s3_client
    )

# 파일 업로더 객체 반환 함수
def get_file_uploader():
    """파일 업로더 객체 반환"""
    from src.uploads.file_uploader import FileUploader
    storage = get_storage()
    return FileUploader(storage=storage)


