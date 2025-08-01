# -*- coding: utf-8 -*-
"""
파일 업로더 모듈
다양한 파일 타입의 업로드를 통합 관리하는 모듈
"""

import os
import tempfile
import mimetypes
from typing import Dict, Any, Optional, Union
from pathlib import Path

from .s3_storage import S3Storage, S3StorageError


class FileUploaderError(Exception):
    """파일 업로더 관련 오류"""
    pass


class VideoUploadError(FileUploaderError):
    """동영상 업로드 관련 오류"""
    pass


class UnsupportedVideoFormatError(VideoUploadError):
    """지원하지 않는 동영상 형식 오류"""
    pass


class VideoFileSizeError(VideoUploadError):
    """동영상 파일 크기 오류"""
    pass


class FileUploader:
    """
    통합 파일 업로더 클래스
    다양한 파일 타입의 업로드를 S3로 처리
    """
    
    def __init__(self, storage: S3Storage):
        """
        FileUploader 초기화
        
        :param storage: S3Storage 인스턴스
        """
        self.storage = storage
        
        # 동영상 관련 상수 초기화
        self.SUPPORTED_VIDEO_FORMATS = {
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
            '.wmv': 'video/x-ms-wmv',
            '.flv': 'video/x-flv',
            '.webm': 'video/webm',
            '.mkv': 'video/x-matroska',
            '.m4v': 'video/x-m4v',
            '.3gp': 'video/3gpp',
            '.ogv': 'video/ogg'
        }
        self.MAX_VIDEO_FILE_SIZE = 500 * 1024 * 1024  # 500MB
        
        # 지원되는 파일 타입 정의
        self.supported_types = {
            'video': list(self.SUPPORTED_VIDEO_FORMATS.keys()),
            'document': ['.doc', '.docx', '.txt', '.rtf'],
            'presentation': ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        }
    
    def upload_video(self, file_path: str, validate: bool = True, max_file_size: Optional[int] = None) -> Dict[str, Any]:
        """
        동영상 파일을 S3에 업로드
        
        :param file_path: 업로드할 동영상 파일 경로
        :param validate: 파일 유효성 검증 여부
        :param max_file_size: 최대 파일 크기 (바이트), None이면 기본값 사용
        :return: 업로드 결과
        :raises FileUploaderError: 업로드 실패 시
        """
        try:
            # 파일 유효성 검증 (옵션)
            if validate:
                validation_result = self.validate_video_file(file_path, max_file_size)
                if not validation_result.get('is_valid', False):
                    raise FileUploaderError("동영상 파일 유효성 검증 실패")
            
            # S3에 업로드
            upload_result = self.storage.upload_file(
                file_path=file_path,
                content_type=self._get_video_content_type(file_path)
            )
            
            return {
                "success": True,
                "file_type": "video",
                "s3_url": upload_result["s3_url"],
                "https_url": upload_result["https_url"],
                "s3_key": upload_result["s3_key"],
                "file_size": upload_result["file_size"],
                "original_filename": upload_result["original_filename"],
                "content_type": upload_result["content_type"]
            }
            
        except (VideoUploadError, UnsupportedVideoFormatError, VideoFileSizeError) as e:
            raise FileUploaderError(f"동영상 업로드 실패: {str(e)}")
        except S3StorageError as e:
            raise FileUploaderError(f"S3 업로드 실패: {str(e)}")
        except Exception as e:
            raise FileUploaderError(f"동영상 업로드 중 예상치 못한 오류: {str(e)}")
    
    def upload_document(self, file_path: str) -> Dict[str, Any]:
        """
        문서 파일을 S3에 업로드
        
        :param file_path: 업로드할 문서 파일 경로
        :return: 업로드 결과
        :raises FileUploaderError: 업로드 실패 시
        """
        try:
            # 문서 파일 유효성 검증
            self._validate_document_file(file_path)
            
            # S3에 업로드
            upload_result = self.storage.upload_file(
                file_path=file_path,
                content_type=self._get_document_content_type(file_path)
            )
            
            return {
                "success": True,
                "file_type": "document",
                "s3_url": upload_result["s3_url"],
                "https_url": upload_result["https_url"],
                "s3_key": upload_result["s3_key"],
                "file_size": upload_result["file_size"],
                "original_filename": upload_result["original_filename"],
                "content_type": upload_result["content_type"]
            }
            
        except S3StorageError as e:
            raise FileUploaderError(f"S3 업로드 실패: {str(e)}")
        except Exception as e:
            raise FileUploaderError(f"문서 업로드 중 예상치 못한 오류: {str(e)}")
    
    def upload_presentation(self, file_path: str) -> Dict[str, Any]:
        """
        프레젠테이션 파일을 S3에 업로드
        
        :param file_path: 업로드할 프레젠테이션 파일 경로
        :return: 업로드 결과
        :raises FileUploaderError: 업로드 실패 시
        """
        try:
            # 프레젠테이션 파일 유효성 검증
            self._validate_presentation_file(file_path)
            
            # S3에 업로드
            upload_result = self.storage.upload_file(
                file_path=file_path,
                content_type=self._get_presentation_content_type(file_path)
            )
            
            return {
                "success": True,
                "file_type": "presentation",
                "s3_url": upload_result["s3_url"],
                "https_url": upload_result["https_url"],
                "s3_key": upload_result["s3_key"],
                "file_size": upload_result["file_size"],
                "original_filename": upload_result["original_filename"],
                "content_type": upload_result["content_type"]
            }
            
        except S3StorageError as e:
            raise FileUploaderError(f"S3 업로드 실패: {str(e)}")
        except Exception as e:
            raise FileUploaderError(f"프레젠테이션 업로드 중 예상치 못한 오류: {str(e)}")
    
    def upload_file_auto(self, file_path: str) -> Dict[str, Any]:
        """
        파일 타입을 자동 감지하여 업로드
        
        :param file_path: 업로드할 파일 경로
        :return: 업로드 결과
        :raises FileUploaderError: 업로드 실패 시
        """
        try:
            file_type = self._detect_file_type(file_path)
            
            if file_type == 'video':
                return self.upload_video(file_path)
            elif file_type == 'document':
                return self.upload_document(file_path)
            elif file_type == 'presentation':
                return self.upload_presentation(file_path)
            else:
                raise FileUploaderError(f"지원하지 않는 파일 타입입니다: {file_type}")
                
        except Exception as e:
            raise FileUploaderError(f"자동 업로드 실패: {str(e)}")
    
    def delete_file(self, s3_key: str) -> Dict[str, Any]:
        """
        S3에서 파일 삭제
        
        :param s3_key: 삭제할 S3 객체 키
        :return: 삭제 결과
        """
        try:
            return self.storage.delete_file(s3_key)
        except S3StorageError as e:
            raise FileUploaderError(f"파일 삭제 실패: {str(e)}")
    
    def get_file_info(self, s3_key: str) -> Dict[str, Any]:
        """
        S3 파일 정보 조회
        
        :param s3_key: 조회할 S3 객체 키
        :return: 파일 정보
        """
        try:
            return self.storage.get_file_info(s3_key)
        except S3StorageError as e:
            raise FileUploaderError(f"파일 정보 조회 실패: {str(e)}")
    
    def _detect_file_type(self, file_path: str) -> str:
        """파일 확장자를 기반으로 파일 타입 감지"""
        file_extension = Path(file_path).suffix.lower()
        
        for file_type, extensions in self.supported_types.items():
            if file_extension in extensions:
                return file_type
        
        return 'unknown'
    
    def _validate_document_file(self, file_path: str) -> None:
        """문서 파일 유효성 검증"""
        if not os.path.exists(file_path):
            raise FileUploaderError(f"파일을 찾을 수 없습니다: {file_path}")
        
        file_extension = Path(file_path).suffix.lower()
        if file_extension not in self.supported_types['document']:
            supported = ', '.join(self.supported_types['document'])
            raise FileUploaderError(f"지원하지 않는 문서 형식입니다. 지원 형식: {supported}")
        
        # 파일 크기 검증 (100MB 제한)
        file_size = os.path.getsize(file_path)
        max_size = 100 * 1024 * 1024  # 100MB
        if file_size > max_size:
            raise FileUploaderError(f"파일 크기가 너무 큽니다. 최대 크기: {max_size // (1024*1024)}MB")
    
    def _validate_presentation_file(self, file_path: str) -> None:
        """프레젠테이션 파일 유효성 검증"""
        if not os.path.exists(file_path):
            raise FileUploaderError(f"파일을 찾을 수 없습니다: {file_path}")
        
        file_extension = Path(file_path).suffix.lower()
        if file_extension not in self.supported_types['presentation']:
            supported = ', '.join(self.supported_types['presentation'])
            raise FileUploaderError(f"지원하지 않는 프레젠테이션 형식입니다. 지원 형식: {supported}")
        
        # 파일 크기 검증 (200MB 제한)
        file_size = os.path.getsize(file_path)
        max_size = 200 * 1024 * 1024  # 200MB
        if file_size > max_size:
            raise FileUploaderError(f"파일 크기가 너무 큽니다. 최대 크기: {max_size // (1024*1024)}MB")
    
    def _get_video_content_type(self, file_path: str) -> str:
        """동영상 파일의 Content-Type 반환"""
        file_extension = Path(file_path).suffix.lower()
        return self.SUPPORTED_VIDEO_FORMATS.get(file_extension, 'video/mp4')
    
    def _get_document_content_type(self, file_path: str) -> str:
        """문서 파일의 Content-Type 반환"""
        file_extension = Path(file_path).suffix.lower()
        content_types = {
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.rtf': 'application/rtf'
        }
        return content_types.get(file_extension, 'application/octet-stream')
    
    def _get_presentation_content_type(self, file_path: str) -> str:
        """프레젠테이션 파일의 Content-Type 반환"""
        file_extension = Path(file_path).suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.webp': 'image/webp'
        }
        return content_types.get(file_extension, 'application/octet-stream')
        
    # 동영상 검증 관련 메서드
    def validate_video_file(self, file_path: str, max_file_size: Optional[int] = None) -> Dict[str, Any]:
        """
        동영상 파일 유효성 검증
        
        :param file_path: 검증할 파일 경로
        :param max_file_size: 최대 파일 크기 (바이트), None이면 기본값 사용
        :return: 검증 결과
        :raises VideoUploadError: 파일 검증 실패 시
        """
        try:
            max_size = max_file_size or self.MAX_VIDEO_FILE_SIZE
            
            # 파일 존재 여부 확인
            if not os.path.exists(file_path):
                raise VideoUploadError(f"파일을 찾을 수 없습니다: {file_path}")
            
            # 파일 정보 수집
            file_info = self._get_video_file_info(file_path)
            
            # 파일 형식 검증
            self._validate_video_file_format(file_info)
            
            # 파일 크기 검증
            self._validate_video_file_size(file_info, max_size)
            
            # 파일 접근 권한 검증
            self._validate_file_access(file_path)
            
            return {
                "is_valid": True,
                "file_info": file_info,
                "validation_message": "동영상 파일이 유효합니다"
            }
            
        except VideoUploadError:
            raise
        except Exception as e:
            raise VideoUploadError(f"파일 검증 중 예상치 못한 오류 발생: {str(e)}")
    
    def validate_s3_uri(self, s3_uri: str) -> Dict[str, Any]:
        """
        S3 URI 유효성 검증
        
        :param s3_uri: 검증할 S3 URI
        :return: 검증 결과
        """
        try:
            # 기본 URI 형식 검증
            if not s3_uri or not s3_uri.strip():
                raise VideoUploadError("S3 URI가 제공되지 않았습니다")
            
            uri = s3_uri.strip()
            
            # S3 URI 형식 검증
            if not (uri.startswith('s3://') or uri.startswith('https://s3')):
                raise VideoUploadError("올바른 S3 URI 형식이 아닙니다 (s3:// 또는 https://s3로 시작해야 함)")
            
            # 파일 확장자 검증
            if '.' not in uri:
                raise VideoUploadError("S3 URI에 파일 확장자가 필요합니다")
            
            # 동영상 파일 확장자 검증
            file_extension = self._extract_file_extension(uri)
            if file_extension not in self.SUPPORTED_VIDEO_FORMATS:
                supported_formats = ', '.join(self.SUPPORTED_VIDEO_FORMATS.keys())
                raise UnsupportedVideoFormatError(
                    f"지원하지 않는 동영상 형식입니다. "
                    f"현재 확장자: {file_extension}, "
                    f"지원 형식: {supported_formats}"
                )
            
            return {
                "is_valid": True,
                "uri": uri,
                "file_extension": file_extension,
                "mime_type": self.SUPPORTED_VIDEO_FORMATS[file_extension],
                "validation_message": "S3 URI가 유효합니다"
            }
            
        except VideoUploadError:
            raise
        except Exception as e:
            raise VideoUploadError(f"S3 URI 검증 중 오류 발생: {str(e)}")
    
    def get_video_supported_formats(self) -> Dict[str, str]:
        """
        지원되는 동영상 형식 목록 반환
        
        :return: 지원 형식 딕셔너리 (확장자: MIME 타입)
        """
        return self.SUPPORTED_VIDEO_FORMATS.copy()

    def get_video_format_info(self) -> Dict[str, Any]:
        """
        동영상 형식 정보 반환
        
        :return: 형식 정보
        """
        return {
            "supported_formats": list(self.SUPPORTED_VIDEO_FORMATS.keys()),
            "max_file_size_mb": self.MAX_VIDEO_FILE_SIZE // (1024 * 1024),
            "max_file_size_bytes": self.MAX_VIDEO_FILE_SIZE,
            "format_descriptions": {
                ".mp4": "MPEG-4 비디오 (권장)",
                ".mov": "QuickTime 비디오",
                ".avi": "Audio Video Interleave",
                ".wmv": "Windows Media Video",
                ".webm": "WebM 비디오",
                ".mkv": "Matroska 비디오"
            }
        }
    
    def _get_video_file_info(self, file_path: str) -> Dict[str, Any]:
        """동영상 파일 정보 수집"""
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

    def _validate_video_file_format(self, file_info: Dict[str, Any]) -> None:
        """동영상 파일 형식 검증"""
        file_extension = file_info.get("file_extension", "").lower()
        
        if not file_extension:
            raise VideoUploadError("파일 확장자를 확인할 수 없습니다")
        
        if file_extension not in self.SUPPORTED_VIDEO_FORMATS:
            supported_formats = ', '.join(self.SUPPORTED_VIDEO_FORMATS.keys())
            raise UnsupportedVideoFormatError(
                f"지원하지 않는 동영상 형식입니다. "
                f"현재 확장자: {file_extension}, "
                f"지원 형식: {supported_formats}"
            )

    def _validate_video_file_size(self, file_info: Dict[str, Any], max_file_size: int) -> None:
        """동영상 파일 크기 검증"""
        file_size = file_info.get("file_size", 0)
        
        if file_size == 0:
            raise VideoUploadError("파일이 비어있습니다")
        
        if file_size > max_file_size:
            max_size_mb = max_file_size // (1024 * 1024)
            current_size_mb = file_size // (1024 * 1024)
            raise VideoFileSizeError(
                f"파일 크기가 너무 큽니다. "
                f"현재 크기: {current_size_mb}MB, "
                f"최대 허용 크기: {max_size_mb}MB"
            )

    def _validate_file_access(self, file_path: str) -> None:
        """파일 접근 권한 검증"""
        if not os.access(file_path, os.R_OK):
            raise VideoUploadError("파일을 읽을 수 있는 권한이 없습니다")

    def _extract_file_extension(self, uri: str) -> str:
        """URI에서 파일 확장자 추출"""
        # URL 파라미터 제거
        uri_without_params = uri.split('?')[0]
        
        # 파일 확장자 추출
        if '.' in uri_without_params:
            return '.' + uri_without_params.split('.')[-1].lower()
        
        return ""