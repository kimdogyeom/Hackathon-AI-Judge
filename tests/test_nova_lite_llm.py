# -*- coding: utf-8 -*-
"""
NovaLiteLLM 단위 테스트
"""

import pytest
from src.llm.nova_lite_llm import NovaLiteLLM, InvalidInputError, UnsupportedFileTypeError


class TestNovaLiteLLM:
    """NovaLiteLLM 클래스 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.llm = NovaLiteLLM()
    
    def test_init_default_model(self):
        """기본 모델 ID로 초기화 테스트"""
        llm = NovaLiteLLM()
        assert llm.model_id == "amazon.nova-lite-v1:0"
    
    def test_init_custom_model(self):
        """커스텀 모델 ID로 초기화 테스트"""
        custom_model = "amazon.nova-lite-v2:0"
        llm = NovaLiteLLM(model_id=custom_model)
        assert llm.model_id == custom_model
    
    def test_text_only_invoke(self):
        """텍스트 전용 호출 테스트"""
        user_message = "안녕하세요, 테스트 메시지입니다."
        system_message = "당신은 도움이 되는 AI 어시스턴트입니다."
        
        result = self.llm.invoke(
            user_message=user_message,
            system_message=system_message,
            temperature=0.1,
            max_tokens=100
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_legacy_parameter_mapping(self):
        """기존 파라미터 매핑 테스트 (하위 호환성)"""
        prompt = "테스트 프롬프트"
        system_prompt = "시스템 프롬프트"
        
        result = self.llm.invoke(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=100
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_multimodal_invoke(self):
        """멀티모달 호출 테스트 (S3 URI 포함)"""
        user_message = "이 문서를 분석해주세요."
        s3_uri = "https://s3.us-east-1.amazonaws.com/victor.kim-temporary/hackathon/carenity.pdf"
        
        result = self.llm.invoke(
            user_message=user_message,
            s3_uri=s3_uri,
            temperature=0.1,
            max_tokens=200
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_s3_uri_only_invoke(self):
        """S3 URI만으로 호출 테스트"""
        s3_uri = "https://s3.us-east-1.amazonaws.com/victor.kim-temporary/hackathon/carenity.pdf"
        
        result = self.llm.invoke(s3_uri=s3_uri, temperature=0.1, max_tokens=100)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_empty_user_message_error(self):
        """빈 사용자 메시지 오류 테스트"""
        with pytest.raises(InvalidInputError, match="user_message 또는 s3_uri 중 하나는 반드시 제공되어야 합니다"):
            self.llm.invoke(user_message="")
    
    def test_none_user_message_error(self):
        """None 사용자 메시지 오류 테스트"""
        with pytest.raises(InvalidInputError, match="user_message 또는 s3_uri 중 하나는 반드시 제공되어야 합니다"):
            self.llm.invoke(user_message=None)
    
    def test_invalid_s3_uri_error(self):
        """잘못된 S3 URI 오류 테스트"""
        with pytest.raises(InvalidInputError, match="올바른 S3 URI 형식이 아닙니다"):
            self.llm.invoke(user_message="테스트", s3_uri="invalid-uri")
    
    def test_empty_s3_uri_error(self):
        """빈 S3 URI 오류 테스트"""
        with pytest.raises(InvalidInputError, match="S3 URI는 빈 문자열일 수 없습니다"):
            self.llm.invoke(user_message="테스트", s3_uri="")
    
    def test_no_file_extension_error(self):
        """파일 확장자 없는 S3 URI 오류 테스트"""
        with pytest.raises(InvalidInputError, match="S3 URI에 파일 확장자가 필요합니다"):
            self.llm.invoke(user_message="테스트", s3_uri="s3://bucket/file")
    
    def test_unsupported_file_type_error(self):
        """지원되지 않는 파일 타입 오류 테스트"""
        with pytest.raises(UnsupportedFileTypeError, match="지원되지 않는 파일 확장자: xyz"):
            self.llm.invoke(user_message="테스트", s3_uri="s3://bucket/file.xyz")
    
    def test_supported_document_types(self):
        """지원되는 문서 타입 테스트"""
        supported_docs = ['txt', 'md', 'pdf', 'docx', 'doc', 'rtf']
        
        for ext in supported_docs:
            s3_uri = f"s3://bucket/file.{ext}"
            file_type = self.llm._determine_file_type(s3_uri)
            assert file_type == "document"
    
    def test_supported_image_types(self):
        """지원되는 이미지 타입 테스트"""
        supported_images = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
        
        for ext in supported_images:
            s3_uri = f"s3://bucket/file.{ext}"
            file_type = self.llm._determine_file_type(s3_uri)
            assert file_type == "image"
    
    def test_supported_video_types(self):
        """지원되는 비디오 타입 테스트"""
        supported_videos = ['mp4', 'mov', 'avi', 'wmv', 'flv', 'webm', 'mkv']
        
        for ext in supported_videos:
            s3_uri = f"s3://bucket/file.{ext}"
            file_type = self.llm._determine_file_type(s3_uri)
            assert file_type == "video"
    
    def test_case_insensitive_file_extension(self):
        """대소문자 구분 없는 파일 확장자 테스트"""
        s3_uri_upper = "s3://bucket/file.PDF"
        s3_uri_lower = "s3://bucket/file.pdf"
        
        file_type_upper = self.llm._determine_file_type(s3_uri_upper)
        file_type_lower = self.llm._determine_file_type(s3_uri_lower)
        
        assert file_type_upper == file_type_lower == "document"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])