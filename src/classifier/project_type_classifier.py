# -*- coding: utf-8 -*-
import yaml
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

from src.config.config_manager import get_config_manager
from src.llm.nova_lite_llm import NovaLiteLLM

logger = logging.getLogger(__name__)


class ProjectTypeClassifier:
    """
    프로젝트 자료를 분석하여 PainKiller/Vitamin/Balanced 유형을 분류하는 클래스 (LLM 기반)
    """
    
    def __init__(self, config_path: str = None):
        """
        분류기 초기화
        
        Args:
            config_path (str, optional): 설정 파일 경로. None이면 기본 경로 사용
        """
        if config_path is None:
            config_dir = Path(__file__).parent.parent / "config" / "settings" / "evaluation"
            config_path = config_dir / "project_classification.yaml"
        
        self.config = self._load_config(config_path)
        self.confidence_threshold = self.config["classification"]["confidence_threshold"]
        self.config_manager = get_config_manager()
        
        # LLM 관련 설정 로드
        self.llm_config = self.config_manager.get_config('llm_classification.yaml', 'llm_classification', {})
        nova_lite_config = self.llm_config.get('llm_config', {}).get('nova_lite', {})
        self.llm_client = NovaLiteLLM(model_id=nova_lite_config.get('model_id', 'amazon.nova-lite-v1:0'))
        
        # 프롬프트 템플릿 로드
        self.prompts = self.config_manager.get_config('system_prompts.yaml', 'project_classification', {})
        self.system_prompt = self.prompts.get('system_prompt', '')
        self.user_prompt_template = self.prompts.get('user_prompt', '')
        self.simple_retry_prompt = self.prompts.get('simple_retry_prompt', '')
        self.regex_patterns = self.prompts.get('regex_patterns', {})
        
    def _load_config(self, config_path: Path) -> Dict:
        """
        설정 파일을 로드합니다.
        
        Args:
            config_path (Path): 설정 파일 경로
            
        Returns:
            Dict: 설정 데이터
            
        Raises:
            FileNotFoundError: 설정 파일을 찾을 수 없는 경우
            ValueError: YAML 파싱 오류가 발생한 경우
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"프로젝트 분류 설정 파일을 찾을 수 없습니다: {config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"설정 파일 YAML 파싱 오류: {e}")
    
    def classify(self, analysis_data: Dict) -> Dict:
        """
        프로젝트 자료를 분석하여 유형을 분류합니다. (LLM 기반)
        
        Args:
            analysis_data (Dict): 분석된 프로젝트 데이터
                - video_analysis: 비디오 분석 결과
                - document_analysis: 문서 분석 결과  
                - presentation_analysis: 발표자료 분석 결과
                
        Returns:
            Dict: 분류 결과
                - project_type: "painkiller" | "vitamin" | "balanced"
                - confidence: 신뢰도 (0.0 - 1.0)
                - painkiller_score: PainKiller 점수 (0.0 - 1.0)
                - vitamin_score: Vitamin 점수 (0.0 - 1.0)
                - reasoning: 분류 근거
                - warning_message: 경고 메시지 (필요시)
        """
        try:
            logger.info("LLM 기반 프로젝트 유형 분류 시작")
            
            # LLM을 사용한 분류 수행
            llm_response = self._call_llm_for_classification(analysis_data)
            
            # 응답 파싱 시도
            parsed_result = self._parse_llm_response(llm_response)
            
            # 결과 검증 및 표준화
            result = self._validate_classification_result(parsed_result)
            
            logger.info(f"프로젝트 유형 분류 완료: {result['project_type']} (신뢰도: {result['confidence']:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"프로젝트 유형 분류 중 오류 발생: {e}")
            self._handle_classification_failure(e)
    
    def _call_llm_for_classification(self, analysis_data: Dict) -> str:
        """
        LLM을 호출하여 분류를 수행합니다.
        
        Args:
            analysis_data (Dict): 분석 데이터
            
        Returns:
            str: LLM 응답
        """
        # 분석 데이터를 프롬프트용으로 포맷팅
        formatted_data = self._format_analysis_data(analysis_data)
        
        # 사용자 프롬프트 생성
        user_prompt = self.user_prompt_template.format(analysis_data=formatted_data)
        
        # LLM 호출 설정
        nova_lite_config = self.llm_config.get('llm_config', {}).get('nova_lite', {})
        
        # LLM 호출
        response = self.llm_client.invoke(
            user_message=user_prompt,
            system_message=self.system_prompt,
            temperature=nova_lite_config.get('temperature', 0.3),
            max_tokens=nova_lite_config.get('max_tokens', 2000)
        )
        
        logger.debug(f"LLM 응답 길이: {len(response)} 문자")
        return response
    
    def _parse_llm_response(self, response: str) -> Dict:
        """
        LLM 응답을 파싱하여 분류 결과를 추출합니다.
        
        Args:
            response (str): LLM 응답
            
        Returns:
            Dict: 파싱된 분류 결과
        """
        # JSON 형식 응답 파싱 시도
        try:
            # JSON 블록 추출
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # JSON 블록이 없으면 전체 응답에서 JSON 찾기
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("JSON 형식을 찾을 수 없습니다")
            
            # JSON 파싱
            parsed_result = json.loads(json_str)
            logger.debug("JSON 파싱 성공")
            return parsed_result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"JSON 파싱 실패: {e}")
            
            # 파싱 실패시 재시도 로직
            parsing_config = self.llm_config.get('parsing_config', {})
            if parsing_config.get('use_simpler_prompt_on_retry', True):
                return self._retry_with_simpler_prompt(response)
            else:
                return self._extract_with_regex(response)
    
    def _retry_with_simpler_prompt(self, original_response: str) -> Dict:
        """
        파싱 실패시 더 간단한 프롬프트로 재시도합니다.
        
        Args:
            original_response (str): 원본 응답
            
        Returns:
            Dict: 재시도 결과
        """
        max_retries = self.llm_config.get('parsing_config', {}).get('max_parse_retries', 2)
        
        for retry_count in range(max_retries):
            try:
                logger.info(f"간단한 프롬프트로 재시도 {retry_count + 1}/{max_retries}")
                
                # 간단한 프롬프트로 재시도
                simple_prompt = self.simple_retry_prompt.format(
                    analysis_data="이전 분석 결과를 바탕으로 분류해주세요."
                )
                
                nova_lite_config = self.llm_config.get('llm_config', {}).get('nova_lite', {})
                response = self.llm_client.invoke(
                    user_message=simple_prompt,
                    system_message="간단히 JSON 형식으로만 응답하세요.",
                    temperature=nova_lite_config.get('temperature', 0.3),
                    max_tokens=500
                )
                
                # JSON 파싱 재시도
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    parsed_result = json.loads(json_match.group(0))
                    logger.info("재시도 파싱 성공")
                    return parsed_result
                    
            except Exception as e:
                logger.warning(f"재시도 {retry_count + 1} 실패: {e}")
                continue
        
        # 모든 재시도 실패시 정규식 기반 추출
        logger.warning("모든 재시도 실패, 정규식 기반 추출 시도")
        return self._extract_with_regex(original_response)
    
    def _extract_with_regex(self, response: str) -> Dict:
        """
        정규식을 사용하여 응답에서 분류 정보를 추출합니다.
        
        Args:
            response (str): LLM 응답
            
        Returns:
            Dict: 추출된 분류 결과
        """
        result = {}
        
        try:
            # 정규식 패턴으로 각 필드 추출
            for field, pattern in self.regex_patterns.items():
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    
                    # 타입 변환
                    if field in ['confidence', 'painkiller_score', 'vitamin_score']:
                        result[field] = float(value)
                    else:
                        result[field] = value
            
            logger.info("정규식 기반 추출 성공")
            return result
            
        except Exception as e:
            logger.error(f"정규식 추출 실패: {e}")
            raise ValueError("응답 파싱 완전 실패")
    
    def _format_analysis_data(self, analysis_data: Dict) -> str:
        """
        분석 데이터를 프롬프트용으로 포맷팅합니다.
        
        Args:
            analysis_data (Dict): 분석 데이터
            
        Returns:
            str: 포맷팅된 텍스트
        """
        formatted_sections = []
        
        # 각 분석 결과를 구조화된 형태로 포맷팅
        for analysis_type in ["video_analysis", "document_analysis", "presentation_analysis"]:
            analysis_result = analysis_data.get(analysis_type, {})
            
            if analysis_result:
                section_title = {
                    "video_analysis": "## 비디오 분석 결과",
                    "document_analysis": "## 문서 분석 결과", 
                    "presentation_analysis": "## 발표자료 분석 결과"
                }.get(analysis_type, f"## {analysis_type}")
                
                formatted_sections.append(section_title)
                
                if isinstance(analysis_result, dict):
                    # 딕셔너리 형태의 분석 결과를 텍스트로 변환
                    for key, value in analysis_result.items():
                        if isinstance(value, str) and len(value.strip()) > 0:
                            formatted_sections.append(f"**{key}**: {value}")
                        elif isinstance(value, (list, dict)):
                            formatted_sections.append(f"**{key}**: {str(value)}")
                elif isinstance(analysis_result, str):
                    formatted_sections.append(analysis_result)
                
                formatted_sections.append("")  # 빈 줄 추가
        
        return "\n".join(formatted_sections)
    
    def _validate_classification_result(self, parsed_result: Dict) -> Dict:
        """
        분류 결과를 검증하고 표준화합니다.
        
        Args:
            parsed_result (Dict): 파싱된 결과
            
        Returns:
            Dict: 검증된 분류 결과
        """
        # 필수 필드 검증 (기본값 없이)
        required_fields = ["project_type", "confidence", "painkiller_score", "vitamin_score", "reasoning"]
        missing_fields = [field for field in required_fields if field not in parsed_result]
        
        if missing_fields:
            raise ValueError(f"LLM 응답에서 필수 필드가 누락되었습니다: {missing_fields}")
        
        result = {
            "project_type": parsed_result["project_type"],
            "confidence": parsed_result["confidence"],
            "painkiller_score": parsed_result["painkiller_score"],
            "vitamin_score": parsed_result["vitamin_score"],
            "reasoning": parsed_result["reasoning"],
            "warning_message": None
        }
        
        # 값 검증 및 보정
        result["project_type"] = result["project_type"].lower()
        if result["project_type"] not in ["painkiller", "vitamin", "balanced"]:
            result["project_type"] = "balanced"
            result["warning_message"] = "유효하지 않은 프로젝트 유형이 감지되어 Balanced로 설정되었습니다."
        
        # 신뢰도 범위 검증
        result["confidence"] = max(0.0, min(1.0, float(result["confidence"])))
        
        # 점수는 음수만 제한하고 정규화 전에는 상한 제한하지 않음
        result["painkiller_score"] = max(0.0, float(result["painkiller_score"]))
        result["vitamin_score"] = max(0.0, float(result["vitamin_score"]))
        
        # 점수 합계 정규화
        total_score = result["painkiller_score"] + result["vitamin_score"]
        if total_score > 0:
            result["painkiller_score"] = result["painkiller_score"] / total_score
            result["vitamin_score"] = result["vitamin_score"] / total_score
        
        return result
    
    def _handle_classification_failure(self, error: Exception) -> None:
        """
        LLM 분류 실패시 적절한 예외를 발생시킵니다.
        
        Args:
            error (Exception): 발생한 오류
            
        Raises:
            RuntimeError: 분류 실패 오류
        """
        error_handling = self.llm_config.get('error_handling', {})
        raise_on_failure = error_handling.get('raise_on_failure', True)
        
        if raise_on_failure:
            # 원본 오류를 포함한 명확한 예외 발생
            raise RuntimeError(f"프로젝트 분류 실패: {str(error)}") from error
        else:
            # 레거시 지원: 기본값 반환 (권장하지 않음)
            logger.warning("LLM 분류 실패했지만 기본값으로 처리됩니다. 이는 권장되지 않는 동작입니다.")
            return {
                "project_type": "balanced",
                "confidence": 0.0,
                "painkiller_score": 0.5,
                "vitamin_score": 0.5,
                "reasoning": "LLM 분류 실패로 인한 임시 기본값 (수정 필요)",
                "warning_message": f"분류 실패: {str(error)}"
            }

    def get_classification_info(self) -> Dict:
        """
        현재 분류 설정 정보를 반환합니다.
        
        Returns:
            Dict: 분류 설정 정보
        """
        return {
            "method": "llm_based",
            "confidence_threshold": self.confidence_threshold,
            "llm_model": self.llm_config.get('llm_config', {}).get('nova_lite', {}).get('model_id', 'amazon.nova-lite-v1:0'),
            "llm_enabled": self.llm_config.get('enabled', True),
            "parsing_retries": self.llm_config.get('parsing_config', {}).get('max_parse_retries', 2)
        }