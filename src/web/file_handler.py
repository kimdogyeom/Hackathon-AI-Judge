# -*- coding: utf-8 -*-
"""
파일 업로드 및 처리 핸들러
"""
import os
import tempfile
import shutil
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import mimetypes
import hashlib
from datetime import datetime, timedelta

import streamlit as st


class FileHandler:
    """파일 업로드 및 처리를 담당하는 클래스"""
    
    # 파일 크기 제한 (바이트)
    MAX_FILE_SIZES = {
        'document': 10 * 1024 * 1024,    # 10MB
        'presentation': 50 * 1024 * 1024,  # 50MB
        'video': 500 * 1024 * 1024,      # 500MB
    }
    
    # 지원되는 파일 형식
    SUPPORTED_FORMATS = {
        'document': ['.txt', '.doc', '.docx'],
        'presentation': ['.pdf', '.ppt', '.pptx'],
        'video': ['.mp4', '.avi', '.mov'],
    }
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "project_evaluation"
        self.temp_dir.mkdir(exist_ok=True)
        
        # 임시 파일 정리를 위한 스케줄러 (24시간 후 자동 삭제)
        self._cleanup_old_files()
    
    def save_uploaded_files(self, uploaded_files: Dict, session_id: str) -> Dict[str, str]:
        """
        업로드된 파일들을 임시 디렉토리에 저장
        
        Args:
            uploaded_files: 업로드된 파일들 (file_type -> file_object)
            session_id: 세션 ID
            
        Returns:
            파일 경로들 (file_type -> file_path)
            
        Raises:
            ValueError: 파일 검증 실패 시
        """
        session_dir = self.temp_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        file_paths = {}
        
        for file_type, file_obj in uploaded_files.items():
            try:
                # 파일 검증
                self._validate_file(file_obj, file_type)
                
                # 안전한 파일명 생성
                safe_filename = self._generate_safe_filename(file_obj.name, file_type)
                file_path = session_dir / safe_filename
                
                # 파일 저장
                with open(file_path, 'wb') as f:
                    f.write(file_obj.getvalue())
                
                file_paths[file_type] = str(file_path)
                
                # 파일 정보 로깅
                st.write(f"✅ {file_type} 파일 저장 완료: {safe_filename}")
                
            except Exception as e:
                # 오류 발생 시 이미 저장된 파일들 정리
                self._cleanup_session_files(session_id)
                raise ValueError(f"{file_type} 파일 처리 중 오류: {str(e)}")
        
        return file_paths
    
    def _validate_file(self, file_obj, file_type: str) -> None:
        """
        파일 유효성 검증
        
        Args:
            file_obj: 업로드된 파일 객체
            file_type: 파일 타입 ('document', 'presentation', 'video')
            
        Raises:
            ValueError: 검증 실패 시
        """
        # 파일 크기 검증
        file_size = len(file_obj.getvalue())
        max_size = self.MAX_FILE_SIZES.get(file_type, 10 * 1024 * 1024)
        
        if file_size > max_size:
            raise ValueError(
                f"파일 크기가 너무 큽니다. "
                f"최대 {max_size // (1024*1024)}MB까지 지원됩니다. "
                f"현재 파일 크기: {file_size // (1024*1024)}MB"
            )
        
        if file_size == 0:
            raise ValueError("빈 파일은 업로드할 수 없습니다.")
        
        # 파일 확장자 검증
        file_extension = Path(file_obj.name).suffix.lower()
        supported_formats = self.SUPPORTED_FORMATS.get(file_type, [])
        
        if file_extension not in supported_formats:
            raise ValueError(
                f"지원되지 않는 파일 형식입니다. "
                f"지원 형식: {', '.join(supported_formats)}"
            )
        
        # MIME 타입 검증 (추가 보안)
        mime_type, _ = mimetypes.guess_type(file_obj.name)
        if mime_type:
            self._validate_mime_type(mime_type, file_type)
    
    def _validate_mime_type(self, mime_type: str, file_type: str) -> None:
        """MIME 타입 검증"""
        valid_mime_types = {
            'document': [
                'text/plain',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ],
            'presentation': [
                'application/pdf',
                'application/vnd.ms-powerpoint',
                'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            ],
            'video': [
                'video/mp4',
                'video/avi',
                'video/quicktime'
            ]
        }
        
        if file_type in valid_mime_types:
            if mime_type not in valid_mime_types[file_type]:
                st.warning(f"파일 형식 경고: {mime_type}는 예상되지 않은 MIME 타입입니다.")
    
    def _generate_safe_filename(self, original_name: str, file_type: str) -> str:
        """
        안전한 파일명 생성
        
        Args:
            original_name: 원본 파일명
            file_type: 파일 타입
            
        Returns:
            안전한 파일명
        """
        # 파일명에서 위험한 문자 제거
        safe_name = "".join(c for c in original_name if c.isalnum() or c in "._-")
        
        # 파일명이 너무 길면 자르기
        if len(safe_name) > 100:
            name_part = Path(safe_name).stem[:80]
            extension = Path(safe_name).suffix
            safe_name = f"{name_part}{extension}"
        
        # 타임스탬프 추가로 중복 방지
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_part = Path(safe_name).stem
        extension = Path(safe_name).suffix
        
        return f"{file_type}_{timestamp}_{name_part}{extension}"
    
    def get_file_info(self, file_path: str) -> Dict:
        """
        파일 정보 조회
        
        Args:
            file_path: 파일 경로
            
        Returns:
            파일 정보 딕셔너리
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        file_stat = os.stat(file_path)
        file_path_obj = Path(file_path)
        
        return {
            'name': file_path_obj.name,
            'size': file_stat.st_size,
            'extension': file_path_obj.suffix,
            'created_time': datetime.fromtimestamp(file_stat.st_ctime),
            'modified_time': datetime.fromtimestamp(file_stat.st_mtime),
            'checksum': self._calculate_checksum(file_path)
        }
    
    def _calculate_checksum(self, file_path: str) -> str:
        """파일 체크섬 계산"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _cleanup_session_files(self, session_id: str) -> None:
        """특정 세션의 파일들 정리"""
        session_dir = self.temp_dir / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)
    
    def _cleanup_old_files(self) -> None:
        """24시간 이상 된 임시 파일들 정리"""
        if not self.temp_dir.exists():
            return
        
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for session_dir in self.temp_dir.iterdir():
            if session_dir.is_dir():
                try:
                    dir_mtime = datetime.fromtimestamp(session_dir.stat().st_mtime)
                    if dir_mtime < cutoff_time:
                        shutil.rmtree(session_dir)
                except Exception as e:
                    # 정리 실패는 로그만 남기고 계속 진행
                    print(f"임시 파일 정리 실패: {session_dir}, 오류: {e}")
    
    def cleanup_all_temp_files(self) -> None:
        """모든 임시 파일 정리 (테스트용)"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir.mkdir(exist_ok=True)
    
    def get_storage_usage(self) -> Dict:
        """임시 저장소 사용량 조회"""
        if not self.temp_dir.exists():
            return {'total_size': 0, 'file_count': 0, 'session_count': 0}
        
        total_size = 0
        file_count = 0
        session_count = 0
        
        for session_dir in self.temp_dir.iterdir():
            if session_dir.is_dir():
                session_count += 1
                for file_path in session_dir.rglob('*'):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                        file_count += 1
        
        return {
            'total_size': total_size,
            'file_count': file_count,
            'session_count': session_count,
            'total_size_mb': total_size / (1024 * 1024)
        }