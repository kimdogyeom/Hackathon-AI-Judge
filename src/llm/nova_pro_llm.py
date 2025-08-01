# -*- coding: utf-8 -*-
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Optional, List, Dict, Any

from src.llm.base_llm import BaseLLM


class InvalidInputError(Exception):
    """잘못된 입력 파라미터 예외"""
    pass


class UnsupportedFileTypeError(Exception):
    """지원되지 않는 파일 타입 예외"""
    pass


class NovaProLLM(BaseLLM):
    """
    AWS Bedrock Nova Pro 모델 호출을 처리하는 클래스.
    LangChain을 사용하여 표준화된 방식으로 Nova Pro 모델에 접근합니다.
    비디오 분석에 특화된 모델입니다.
    """

    def __init__(self, model_id: str = None):
        """
        NovaProLLM 초기화
        
        :param model_id: 사용할 모델 ID (None이면 설정에서 로드)
        """
        if model_id is None:
            # 설정에서 모델 ID 로드
            try:
                from src.config.config_manager import get_config_manager
                config_manager = get_config_manager()
                llm_config = config_manager.get_config('llm_classification.yaml', 'llm_classification.llm_config', {})
                nova_pro_config = llm_config.get('nova_pro', {})
                model_id = nova_pro_config.get('model_id', 'amazon.nova-pro-v1:0')
            except Exception:
                # 설정 로드 실패시 기본값 사용
                model_id = 'amazon.nova-pro-v1:0'
        
        self.model_id = model_id

    def invoke(self, 
               s3_uri: str = None,
               user_message: str = None,
               system_message: str = None,
               system_prompt: str = None,
               model_id: str = None,
               **kwargs) -> Dict[str, Any]:
        """
        Nova Pro 모델을 호출합니다. 주로 비디오 분석에 사용됩니다.
        
        Args:
            s3_uri: 분석할 비디오 파일의 S3 URI (필수)
            user_message: 사용자 메시지 (선택, 기본값 제공)
            system_message: 시스템 프롬프트 (선택)
            system_prompt: 기존 호환성을 위한 파라미터 (system_message로 매핑)
            model_id: 모델 ID 오버라이드 (선택)
            **kwargs: ChatBedrockConverse model_kwargs (temperature, max_tokens 등)
        
        Returns:
            Dict[str, Any]: 비디오 분석 결과
            
        Raises:
            InvalidInputError: 잘못된 입력 파라미터
            UnsupportedFileTypeError: 지원되지 않는 파일 타입
            RuntimeError: LLM 호출 중 오류 발생
        """
        try:
            # 기존 파라미터 매핑 (하위 호환성)
            if system_prompt is not None and system_message is None:
                system_message = system_prompt
            
            # 모델 ID 오버라이드
            current_model_id = model_id if model_id else self.model_id
            
            # 입력 유효성 검증
            self._validate_input(s3_uri)
            
            # 기본 사용자 메시지 설정
            if not user_message:
                user_message = "이 비디오를 분석하여 주요 내용, 장면, 음성 내용을 요약해주세요."
            
            print(f"[DEBUG] 모델 ID: {current_model_id}")
            print(f"[DEBUG] S3 URI: {s3_uri}")
            print(f"[DEBUG] 시스템 메시지 길이: {len(system_message) if system_message else 0}")
            
            # ChatBedrockConverse 인스턴스 생성
            llm = ChatBedrockConverse(
                model_id=current_model_id,
                **kwargs
            )

            # 멀티모달 메시지 구성 (비디오 + 텍스트)
            messages = self._build_video_analysis_messages(user_message, s3_uri, system_message)
            
            # 모델 호출
            response = llm.invoke(messages)
            
            # 응답 처리 및 구조화
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # 비디오 분석 결과를 구조화된 형태로 반환
            return {
                "analysis_result": content,
                "s3_uri": s3_uri,
                "model_id": current_model_id,
                "analysis_type": "video_analysis"
            }
                
        except (InvalidInputError, UnsupportedFileTypeError):
            # 사용자 입력 오류는 그대로 전파
            raise
        except Exception as e:
            # 기타 오류는 RuntimeError로 래핑
            raise RuntimeError(f"Nova Pro 모델 호출 중 오류 발생: {str(e)}") from e

    def _validate_input(self, s3_uri: str) -> None:
        """
        입력 파라미터 유효성 검증
        
        Args:
            s3_uri: S3 URI (필수)
            
        Raises:
            InvalidInputError: 잘못된 입력 파라미터
            UnsupportedFileTypeError: 지원되지 않는 파일 타입
        """
        # S3 URI는 필수
        if not s3_uri or not s3_uri.strip():
            raise InvalidInputError("비디오 분석을 위해 S3 URI는 필수입니다")
        
        # S3 URI 형식 검증
        if not (s3_uri.startswith('s3://') or s3_uri.startswith('https://s3')):
            raise InvalidInputError("올바른 S3 URI 형식이 아닙니다")
        
        # 파일 확장자 검증
        if '.' not in s3_uri:
            raise InvalidInputError("S3 URI에 파일 확장자가 필요합니다")
        
        # 비디오 파일 타입 검증
        if not self._is_video_file(s3_uri):
            extension = s3_uri.lower().split('.')[-1]
            raise UnsupportedFileTypeError(f"Nova Pro는 비디오 파일만 지원합니다. 현재 확장자: {extension}")

    def _build_video_analysis_messages(self, user_message: str, s3_uri: str, system_message: str = None) -> List:
        """
        비디오 분석용 멀티모달 메시지 구성
        
        Args:
            user_message: 사용자 메시지
            s3_uri: 비디오 파일 S3 URI
            system_message: 시스템 메시지 (선택)
            
        Returns:
            List: LangChain 메시지 객체 리스트
        """
        messages = []
        if system_message and system_message.strip():
            messages.append(SystemMessage(content=system_message))
        
        # Nova Pro 멀티모달 메시지 구성 (비디오 + 텍스트)
        # ChatBedrockConverse에서 비디오를 처리하는 올바른 형식
        multimodal_content = [
            {
                "type": "text",
                "text": user_message
            },
            {
                "type": "video",
                "source": {
                    "type": "s3",
                    "s3_location": {
                        "uri": s3_uri
                    }
                }
            }
        ]
        
        messages.append(HumanMessage(content=multimodal_content))
        
        return messages

    def _is_video_file(self, s3_uri: str) -> bool:
        """
        비디오 파일인지 확인
        
        Args:
            s3_uri: S3 URI
            
        Returns:
            bool: 비디오 파일 여부
        """
        # URI에서 파일 확장자 추출
        file_extension = s3_uri.lower().split('.')[-1] if '.' in s3_uri else ''
        
        # 지원되는 비디오 확장자 정의
        video_extensions = ['mp4', 'mov', 'avi', 'wmv', 'flv', 'webm', 'mkv', 'm4v', '3gp', 'ogv']
        
        return file_extension in video_extensions

