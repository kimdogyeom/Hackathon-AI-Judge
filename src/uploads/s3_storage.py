# -*- coding: utf-8 -*-
"""
S3 스토리지 관리 모듈
AWS S3를 사용한 파일 업로드 및 관리 기능
"""

import os
import uuid
import mimetypes
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class S3StorageError(Exception):
    """S3 스토리지 관련 오류"""
    pass


class S3Storage:
    """
    AWS S3 스토리지 관리 클래스
    파일 업로드, 다운로드, 삭제 등의 기능 제공
    """
    
    def __init__(self, bucket_name: str, s3_client=None):
        """
        S3Storage 초기화
        
        :param bucket_name: S3 버킷 이름
        :param s3_client: boto3 S3 클라이언트 (None이면 자동 생성)
        """
        self.bucket_name = bucket_name
        self.s3_client = s3_client or boto3.client('s3')
        
        # 버킷 존재 여부 확인
        self._verify_bucket_access()
    
    def upload_file(self, file_path: str, s3_key: Optional[str] = None, 
                   content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        로컬 파일을 S3에 업로드
        
        :param file_path: 업로드할 로컬 파일 경로
        :param s3_key: S3 객체 키 (None이면 자동 생성)
        :param content_type: 파일의 MIME 타입 (None이면 자동 감지)
        :return: 업로드 결과 정보
        :raises S3StorageError: 업로드 실패 시
        """
        try:
            # 파일 존재 여부 확인
            if not os.path.exists(file_path):
                raise S3StorageError(f"파일을 찾을 수 없습니다: {file_path}")
            
            # S3 키 생성 (제공되지 않은 경우)
            if s3_key is None:
                s3_key = self._generate_s3_key(file_path)
            
            # Content-Type 자동 감지
            if content_type is None:
                content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            
            # 파일 업로드
            extra_args = {
                'ContentType': content_type,
                'ServerSideEncryption': 'AES256'  # 서버 측 암호화
            }
            
            self.s3_client.upload_file(
                file_path, 
                self.bucket_name, 
                s3_key,
                ExtraArgs=extra_args
            )
            
            # S3 URL 생성
            s3_url = f"s3://{self.bucket_name}/{s3_key}"
            https_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            
            # 파일 정보 수집
            file_info = self._get_file_info(file_path)
            
            return {
                "success": True,
                "s3_key": s3_key,
                "s3_url": s3_url,
                "https_url": https_url,
                "bucket_name": self.bucket_name,
                "content_type": content_type,
                "file_size": file_info["file_size"],
                "original_filename": file_info["file_name"]
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            raise S3StorageError(f"S3 업로드 실패 ({error_code}): {str(e)}")
        except NoCredentialsError:
            raise S3StorageError("AWS 자격 증명을 찾을 수 없습니다")
        except Exception as e:
            raise S3StorageError(f"파일 업로드 중 예상치 못한 오류: {str(e)}")
    
    def delete_file(self, s3_key: str) -> Dict[str, Any]:
        """
        S3에서 파일 삭제
        
        :param s3_key: 삭제할 S3 객체 키
        :return: 삭제 결과
        :raises S3StorageError: 삭제 실패 시
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            
            return {
                "success": True,
                "s3_key": s3_key,
                "message": "파일이 성공적으로 삭제되었습니다"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            raise S3StorageError(f"S3 파일 삭제 실패 ({error_code}): {str(e)}")
        except Exception as e:
            raise S3StorageError(f"파일 삭제 중 예상치 못한 오류: {str(e)}")
    
    def file_exists(self, s3_key: str) -> bool:
        """
        S3에 파일이 존재하는지 확인
        
        :param s3_key: 확인할 S3 객체 키
        :return: 파일 존재 여부
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise S3StorageError(f"파일 존재 여부 확인 실패: {str(e)}")
    
    def get_file_info(self, s3_key: str) -> Dict[str, Any]:
        """
        S3 파일 정보 조회
        
        :param s3_key: 조회할 S3 객체 키
        :return: 파일 정보
        :raises S3StorageError: 조회 실패 시
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            return {
                "s3_key": s3_key,
                "file_size": response.get('ContentLength', 0),
                "content_type": response.get('ContentType', ''),
                "last_modified": response.get('LastModified'),
                "etag": response.get('ETag', '').strip('"'),
                "server_side_encryption": response.get('ServerSideEncryption', ''),
                "s3_url": f"s3://{self.bucket_name}/{s3_key}",
                "https_url": f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise S3StorageError(f"파일을 찾을 수 없습니다: {s3_key}")
            raise S3StorageError(f"파일 정보 조회 실패 ({error_code}): {str(e)}")
    
    def _verify_bucket_access(self) -> None:
        """버킷 접근 권한 확인"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise S3StorageError(f"버킷을 찾을 수 없습니다: {self.bucket_name}")
            elif error_code == '403':
                raise S3StorageError(f"버킷에 접근할 권한이 없습니다: {self.bucket_name}")
            else:
                raise S3StorageError(f"버킷 접근 확인 실패 ({error_code}): {str(e)}")
        except NoCredentialsError:
            raise S3StorageError("AWS 자격 증명을 찾을 수 없습니다")
    
    def _generate_s3_key(self, file_path: str) -> str:
        """
        파일 경로를 기반으로 고유한 S3 키 생성
        
        :param file_path: 원본 파일 경로
        :return: 생성된 S3 키
        """
        file_name = Path(file_path).name
        file_extension = Path(file_path).suffix
        
        # UUID를 사용하여 고유한 키 생성
        unique_id = str(uuid.uuid4())
        
        # 파일 타입별 폴더 구조
        if file_extension.lower() in ['.mp4', '.mov', '.avi', '.wmv', '.webm', '.mkv', '.flv', '.m4v', '.3gp', '.ogv']:
            folder = 'videos'
        elif file_extension.lower() in ['.doc', '.docx', '.txt', '.rtf']:
            folder = 'documents'
        elif file_extension.lower() in ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
            folder = 'presentations'
        else:
            folder = 'others'
        
        return f"{folder}/{unique_id}_{file_name}"
    
    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """로컬 파일 정보 수집"""
        path_obj = Path(file_path)
        stat_info = os.stat(file_path)
        
        return {
            "file_path": file_path,
            "file_name": path_obj.name,
            "file_size": stat_info.st_size,
            "file_extension": path_obj.suffix.lower(),
            "mime_type": mimetypes.guess_type(file_path)[0],
            "last_modified": stat_info.st_mtime
        }