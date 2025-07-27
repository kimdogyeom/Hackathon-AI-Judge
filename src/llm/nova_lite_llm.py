# -*- coding: utf-8 -*-
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Optional, List, Dict, Any

from src.llm.base_llm import BaseLLM

# 캐싱은 일시적으로 비활성화 (순환 참조 문제 해결을 위해)
# from langchain.globals import set_llm_cache
# from langchain_community.cache import InMemoryCache
# set_llm_cache(InMemoryCache())


class InvalidInputError(Exception):
    """잘못된 입력 파라미터 예외"""
    pass


class UnsupportedFileTypeError(Exception):
    """지원되지 않는 파일 타입 예외"""
    pass


class NovaLiteLLM(BaseLLM):
    """
    AWS Bedrock Nova Lite 모델 호출을 처리하는 클래스.
    LangChain을 사용하여 표준화된 방식으로 Nova Lite 모델에 접근합니다.
    """

    def __init__(self, model_id: str = "amazon.nova-lite-v1:0"):
        """
        NovaLiteLLM 초기화
        
        :param model_id: 사용할 모델 ID (nova-lite)
        """
        self.model_id = model_id

    def invoke(self, 
               user_message: str = None,
               system_message: str = None,
               s3_uri: str = None,
               prompt: str = None,
               system_prompt: str = None,
               **kwargs) -> str:
        """
        Nova Lite 모델을 호출합니다.
        
        Args:
            user_message: 사용자 메시지 (필수)
            system_message: 시스템 프롬프트 (선택)
            s3_uri: 멀티모달 입력용 S3 URI (선택)
            prompt: 기존 호환성을 위한 파라미터 (user_message로 매핑)
            system_prompt: 기존 호환성을 위한 파라미터 (system_message로 매핑)
            **kwargs: ChatBedrockConverse model_kwargs (temperature, max_tokens 등)
        
        Returns:
            str: LLM 응답 텍스트
            
        Raises:
            InvalidInputError: 잘못된 입력 파라미터
            UnsupportedFileTypeError: 지원되지 않는 파일 타입
            RuntimeError: LLM 호출 중 오류 발생
        """
        try:
            # 기존 파라미터 매핑 (하위 호환성)
            if prompt is not None and user_message is None:
                user_message = prompt
            if system_prompt is not None and system_message is None:
                system_message = system_prompt
            
            # 입력 유효성 검증
            self._validate_input(user_message, s3_uri)
            
            # user_message가 여전히 None인 경우 기본 메시지 설정 (S3 URI만 있는 경우)
            if not user_message and s3_uri:
                user_message = "이 파일을 분석해주세요."
            
            print(f"[DEBUG] 모델 ID: {self.model_id}")
            print(f"[DEBUG] S3 URI: {s3_uri}")
            print(f"[DEBUG] 시스템 메시지 길이: {len(system_message) if system_message else 0}")
            
            # ChatBedrockConverse 인스턴스 생성
            llm = ChatBedrockConverse(
                model_id=self.model_id,
                **kwargs
            )

            # 메시지 구성
            if s3_uri:
                messages = self._build_multimodal_messages(user_message, s3_uri, system_message)
            else:
                messages = self._build_text_messages(user_message, system_message)
            
            # 모델 호출
            response = llm.invoke(messages)
            
            # 응답에서 텍스트 내용 추출
            if hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
        except (InvalidInputError, UnsupportedFileTypeError):
            # 사용자 입력 오류는 그대로 전파
            raise
        except Exception as e:
            # 기타 오류는 RuntimeError로 래핑
            raise RuntimeError(f"Nova Lite 모델 호출 중 오류 발생: {str(e)}") from e

    def _validate_input(self, user_message: str, s3_uri: str = None) -> None:
        """
        입력 파라미터 유효성 검증
        
        Args:
            user_message: 사용자 메시지
            s3_uri: S3 URI (선택)
            
        Raises:
            InvalidInputError: 잘못된 입력 파라미터
            UnsupportedFileTypeError: 지원되지 않는 파일 타입
        """
        # user_message 또는 s3_uri 중 하나는 반드시 있어야 함
        if (not user_message or not user_message.strip()) and (not s3_uri or not s3_uri.strip()):
            raise InvalidInputError("user_message 또는 s3_uri 중 하나는 반드시 제공되어야 합니다")
        
        # S3 URI 형식 검증
        if s3_uri is not None:
            if not s3_uri.strip():
                raise InvalidInputError("S3 URI는 빈 문자열일 수 없습니다")
            
            if not (s3_uri.startswith('s3://') or s3_uri.startswith('https://s3')):
                raise InvalidInputError("올바른 S3 URI 형식이 아닙니다")
            
            # 파일 확장자 검증
            if '.' not in s3_uri:
                raise InvalidInputError("S3 URI에 파일 확장자가 필요합니다")
            
            # 지원되는 파일 타입 검증
            if not self._is_supported_file_type(s3_uri):
                extension = s3_uri.lower().split('.')[-1]
                raise UnsupportedFileTypeError(f"지원되지 않는 파일 확장자: {extension}")

    def _build_text_messages(self, user_message: str, system_message: str = None) -> List:
        """
        텍스트 전용 메시지 구성
        
        Args:
            user_message: 사용자 메시지
            system_message: 시스템 메시지 (선택)
            
        Returns:
            List: LangChain 메시지 객체 리스트
        """
        messages = []
        if system_message and system_message.strip():
            messages.append(SystemMessage(content=system_message))
        messages.append(HumanMessage(content=user_message))
        return messages

    def _build_multimodal_messages(self, user_message: str, s3_uri: str, system_message: str = None) -> List:
        """
        멀티모달 메시지 구성
        
        Args:
            user_message: 사용자 메시지
            s3_uri: S3 URI
            system_message: 시스템 메시지 (선택)
            
        Returns:
            List: LangChain 메시지 객체 리스트
        """
        messages = []
        if system_message and system_message.strip():
            messages.append(SystemMessage(content=system_message))
        
        # 현재는 임시로 텍스트 형태로 처리 (향후 ChatBedrockConverse 공식 문서 참조하여 개선)
        # TODO: ChatBedrockConverse 공식 문서에서 멀티모달 형식 확인 후 정확한 구현
        multimodal_content = f"{user_message}\n\nS3 URI: {s3_uri}"
        messages.append(HumanMessage(content=multimodal_content))
        
        return messages

    def _is_supported_file_type(self, s3_uri: str) -> bool:
        """
        지원되는 파일 타입인지 확인
        
        Args:
            s3_uri: S3 URI
            
        Returns:
            bool: 지원 여부
        """
        try:
            self._determine_file_type(s3_uri)
            return True
        except:
            return False

    def _determine_file_type(self, s3_uri: str) -> str:
        """
        S3 URI의 파일 확장자를 기반으로 파일 타입을 결정합니다.
        
        Args:
            s3_uri: S3 파일 URI
            
        Returns:
            str: Nova Lite에서 사용할 파일 타입 ("document", "image", "video")
            
        Raises:
            UnsupportedFileTypeError: 지원되지 않는 파일 타입
        """
        # URI에서 파일 확장자 추출
        file_extension = s3_uri.lower().split('.')[-1] if '.' in s3_uri else ''
        
        # 지원되는 파일 확장자 정의
        supported_extensions = {
            'document': ['txt', 'md', 'pdf', 'docx', 'doc', 'rtf'],
            'image': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'],
            'video': ['mp4', 'mov', 'avi', 'wmv', 'flv', 'webm', 'mkv']
        }
        
        for file_type, extensions in supported_extensions.items():
            if file_extension in extensions:
                return file_type
        
        # 지원되지 않는 확장자
        raise UnsupportedFileTypeError(f"지원되지 않는 파일 확장자: {file_extension}")