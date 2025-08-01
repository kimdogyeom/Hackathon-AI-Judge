# -*- coding: utf-8 -*-
"""
평가 체인들이 공통으로 사용하는 유틸리티 함수들을 제공합니다.
business_value_chain.py의 공통 패턴을 추출하여 재사용 가능한 함수로 구현했습니다.
"""

import json
import re
import yaml
from typing import Dict, Any, Optional, List, Union
from langchain_core.runnables.utils import Input

from src.llm.nova_lite_llm import NovaLiteLLM
from src.config.config_manager import get_config_manager


class ChainUtils:
    """평가 체인들이 공통으로 사용하는 유틸리티 함수들을 제공하는 클래스"""
    
    @staticmethod
    def load_evaluation_criteria(config_path: str, criteria_key: str) -> Dict[str, List[str]]:
        """
        YAML 파일에서 평가 기준을 로드합니다.
        
        Args:
            config_path: YAML 설정 파일 경로
            criteria_key: 평가 기준 키 (예: 'BusinessValue', 'Innovation' 등)
            
        Returns:
            Dict: pain_killer와 vitamin 기준을 포함한 딕셔너리
            
        Raises:
            FileNotFoundError: 설정 파일을 찾을 수 없는 경우
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                criteria = yaml.safe_load(file)
            
            evaluation_criteria = criteria.get(criteria_key, {})
            
            return {
                'pain_killer': evaluation_criteria.get('pain_killer', []),
                'vitamin': evaluation_criteria.get('vitamin', [])
            }
            
        except Exception as e:
            print(f"YAML 로드 실패, 기본값 사용: {e}")
            raise FileNotFoundError(f"설정 파일 로드 실패: {config_path} - {e}")
    
    @staticmethod
    def extract_project_type(input_data: Input) -> str:
        """
        입력 데이터에서 프로젝트 타입을 추출합니다.
        
        Args:
            input_data: 입력 데이터 (문자열 또는 딕셔너리)
            
        Returns:
            str: 프로젝트 타입 ('painkiller', 'vitamin', 'balanced')
        """
        project_type = "balanced"  # 기본값
        
        if isinstance(input_data, dict):
            # 직접적인 project_type 필드 확인
            project_type = input_data.get('project_type', 'balanced')
            
            # classification 내부의 project_type 확인
            if 'classification' in input_data and isinstance(input_data['classification'], dict):
                project_type = input_data['classification'].get('project_type', project_type)
        
        return project_type.lower()
    
    @staticmethod
    def process_input_data(input_data: Input) -> str:
        """
        입력 데이터를 처리하여 문자열로 변환합니다.
        
        Args:
            input_data: 입력 데이터 (문자열, 딕셔너리 등)
            
        Returns:
            str: 처리된 프로젝트 정보 문자열
        """
        if isinstance(input_data, str):
            return input_data
        elif isinstance(input_data, dict):
            # 딕셔너리인 경우 주요 필드들을 문자열로 변환
            project_info = ""
            
            # 주요 필드들을 순서대로 처리
            key_mappings = {
                "title": "프로젝트 제목",
                "description": "프로젝트 설명", 
                "content": "내용",
                "summary": "요약",
                "details": "상세 내용"
            }
            
            for key, label in key_mappings.items():
                if key in input_data and input_data[key]:
                    project_info += f"{label}: {input_data[key]}\n"
            
            # 추가 분석 데이터가 있는 경우 포함
            analysis_keys = ["material_analysis", "parsed_data", "video_analysis", 
                           "document_analysis", "presentation_analysis"]
            
            for key in analysis_keys:
                if key in input_data and input_data[key]:
                    analysis_data = input_data[key]
                    if isinstance(analysis_data, dict):
                        content = analysis_data.get('content', analysis_data.get('summary', ''))
                        if content:
                            project_info += f"{key.replace('_', ' ').title()}: {content}\n"
                    else:
                        project_info += f"{key.replace('_', ' ').title()}: {analysis_data}\n"
            
            return project_info if project_info else str(input_data)
        else:
            return str(input_data)
    
    @staticmethod
    def build_system_prompt(criteria_key: str, pain_killer_criteria: List[str], 
                          vitamin_criteria: List[str], project_type: str = "balanced") -> str:
        """
        평가를 위한 시스템 프롬프트를 구성합니다.
        
        Args:
            criteria_key: 평가 기준 키 (예: '비즈니스 가치', '혁신성' 등)
            pain_killer_criteria: Pain Killer 평가 기준 목록
            vitamin_criteria: Vitamin 평가 기준 목록
            project_type: 프로젝트 타입
            
        Returns:
            str: 구성된 시스템 프롬프트
        """
        pain_killer_text = "\n".join([f"- {criteria}" for criteria in pain_killer_criteria])
        vitamin_text = "\n".join([f"- {criteria}" for criteria in vitamin_criteria])
        
        # 프로젝트 타입에 따른 평가
        if project_type.lower() == 'painkiller':
            weight_instruction = f"이 프로젝트는 PainKiller 유형으로 분류되었으므로, Pain Killer 기준에 맞춰 {criteria_key}를 평가하세요."
            evaluation_criteria = pain_killer_text
        elif project_type.lower() == 'vitamin':
            weight_instruction = f"이 프로젝트는 Vitamin 유형으로 분류되었으므로, Vitamin 기준에 맞춰 {criteria_key}를 평가하세요."
            evaluation_criteria = vitamin_text
        else:
            weight_instruction = f"이 프로젝트는 Balanced 유형으로 분류되었으므로, 두 기준을 균등하게 {criteria_key}를 평가하세요."
            evaluation_criteria = pain_killer_text + "\n" + vitamin_text + "\n- 평가항목에 대해서 균등하게 적용할 수 있도록 하세요"
        
        return f"""당신은 {criteria_key} 평가 전문가입니다. 이미 분류된 프로젝트 유형({project_type})을 고려하여 서비스의 {criteria_key}를 평가해주세요.
        
        {weight_instruction}
        
        평가 기준:
        
        **평가기준:**
        {evaluation_criteria}
        
        평가 방법:
        1. 각 기준에 대해 1-10점으로 평가
        2. 프로젝트 타입({project_type})에 따른 평가
        
        **중요: 응답은 반드시 아래 JSON 형식만으로 제공해주세요. 다른 설명이나 텍스트는 포함하지 마세요.**
        
        ```json
        {{
            "score": 숫자,
            "reasoning": "평가에 대한 상세한 근거를 설명, 점수에 대한 명확한 근거가 있어야 하며, 20년차 전문가가 봐도 납득할만한 이유여야 함.",
            "suggestions": ["개선점1", "개선점2", "개선점3"]
        }}
        ```"""
    
    @staticmethod
    def build_user_prompt(project_info: str, criteria_key: str, project_type: str = "balanced") -> str:
        """
        사용자 프롬프트를 구성합니다.
        
        Args:
            project_info: 프로젝트 정보
            criteria_key: 평가 기준 키
            project_type: 프로젝트 타입
            
        Returns:
            str: 구성된 사용자 프롬프트
        """
        return f"""다음 프로젝트의 {criteria_key}를 평가해주세요:

        **프로젝트 분류**: {project_type.upper()} 유형
        **프로젝트 정보**: {project_info}
        
        이미 분류된 프로젝트 유형({project_type})을 고려하여 평가하고, 반드시 JSON 형식으로만 응답해주세요."""
    
    @staticmethod
    def validate_score(score: Any) -> float:
        """
        점수의 유효성을 검증하고 0-10 범위로 제한합니다.
        
        Args:
            score: 검증할 점수 값
            
        Returns:
            float: 0-10 범위의 유효한 점수
        """
        try:
            score_float = float(score)
            return max(0.0, min(10.0, score_float))
        except (ValueError, TypeError):
            print(f"유효하지 않은 점수 값: {score}, 기본값 5.0 사용")
            return 5.0
    
    @staticmethod
    def parse_llm_response(response: str, project_type: str = "balanced") -> Dict[str, Any]:
        """
        LLM 응답을 파싱하여 구조화된 결과로 변환합니다.
        
        Args:
            response: LLM 응답 문자열
            project_type: 프로젝트 타입
            
        Returns:
            Dict: 구조화된 평가 결과
        """
        try:
            # JSON 부분 추출 시도
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                
                # 필수 필드 검증 및 기본값 설정
                result.setdefault("score", 5.0)
                result.setdefault("reasoning", "평가 근거가 제공되지 않았습니다.")
                result.setdefault("suggestions", ["기본 개선 제안", "추가 정보 수집 필요"])
                
                # 점수 유효성 검증
                result["score"] = ChainUtils.validate_score(result["score"])
                
                # reasoning이 비어있는 경우 기본값 설정
                if not result["reasoning"] or result["reasoning"].strip() == "":
                    result["reasoning"] = "평가 근거가 제공되지 않았습니다."
                
                # suggestions가 비어있는 경우 기본값 설정
                if not result["suggestions"] or len(result["suggestions"]) == 0:
                    result["suggestions"] = ["기본 개선 제안", "추가 정보 수집 필요", "평가 기준 재검토"]
                
                # 프로젝트 타입 정보 추가
                result["project_type"] = project_type
                result["evaluation_method"] = "llm_based_with_classification"
                
                return result
            else:
                # JSON 형식이 아닌 경우 fallback 파싱 시도
                return ChainUtils.fallback_parse_response(response, project_type)
                
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"응답 파싱 실패: {e}")
            return ChainUtils.fallback_parse_response(response, project_type)
    
    @staticmethod
    def fallback_parse_response(response: str, project_type: str = "balanced") -> Dict[str, Any]:
        """
        JSON 파싱 실패 시 대체 파싱 방법을 사용합니다.
        
        Args:
            response: LLM 응답 문자열
            project_type: 프로젝트 타입
            
        Returns:
            Dict: 기본 구조화된 결과
        """
        # 점수 패턴 찾기
        score_patterns = [
            r'점수[:\s]*(\d+(?:\.\d+)?)',
            r'score[:\s]*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)[점/점수]',
            r'(\d+(?:\.\d+)?)/10',
            r'(\d+(?:\.\d+)?)점'
        ]
        
        scores = []
        for pattern in score_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            scores.extend([float(match) for match in matches if 0 <= float(match) <= 10])
        
        # 평균 점수 계산 (점수가 있는 경우)
        avg_score = sum(scores) / len(scores) if scores else 5.0
        avg_score = ChainUtils.validate_score(avg_score)
        
        # 개선 제안 추출 시도
        suggestions = []
        suggestion_patterns = [
            r'개선[점사항]*[:\s]*(.+?)(?:\n|$)',
            r'제안[사항]*[:\s]*(.+?)(?:\n|$)',
            r'권장[사항]*[:\s]*(.+?)(?:\n|$)'
        ]
        
        for pattern in suggestion_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE | re.MULTILINE)
            suggestions.extend([match.strip() for match in matches if match.strip()])
        
        # 기본 제안사항이 없는 경우
        if not suggestions:
            suggestions = ["응답 파싱 실패로 인한 기본값", "구조화된 응답 형식 개선 필요", "평가 기준 재검토 권장"]
        
        # reasoning 처리 - 빈 응답인 경우 기본값 제공
        reasoning = response[:500] + "..." if len(response) > 500 else response
        if not reasoning or reasoning.strip() == "":
            reasoning = "응답이 비어있어 평가 근거를 제공할 수 없습니다. 기본 점수를 적용합니다."
        
        return {
            "score": avg_score,
            "reasoning": reasoning,
            "suggestions": suggestions[:3],  # 최대 3개로 제한
            "project_type": project_type,
            "evaluation_method": "fallback_parsed"
        }
    
    @staticmethod
    def handle_llm_error(error: Exception, project_type: str = "balanced") -> Dict[str, Any]:
        """
        LLM 호출 오류를 처리하고 기본 응답을 반환합니다.
        
        Args:
            error: 발생한 오류
            project_type: 프로젝트 타입
            
        Returns:
            Dict: 오류 상황에서의 기본 응답
        """
        return {
            "score": 5.0,
            "reasoning": f"평가 중 오류 발생: {str(error)}. 기본 점수를 제공합니다.",
            "suggestions": ["시스템 관리자에게 문의하세요", "네트워크 연결 상태를 확인하세요", "나중에 다시 시도해보세요"],
            "project_type": project_type,
            "evaluation_method": "error_fallback"
        }
    
    @staticmethod
    def get_llm_config() -> Dict[str, Any]:
        """
        설정에서 LLM 파라미터를 로드합니다.
        
        Returns:
            Dict: LLM 설정 파라미터 (temperature, max_tokens)
        """
        try:
            config_manager = get_config_manager()
            return {
                'temperature': config_manager.get_config('system_config.yaml', 'llm.temperature', 0.3),
                'max_tokens': config_manager.get_config('system_config.yaml', 'llm.max_tokens', 3000)
            }
        except Exception as e:
            print(f"LLM 설정 로드 실패, 기본값 사용: {e}")
            return {
                'temperature': 0.3,
                'max_tokens': 3000
            }


class LLMEvaluator:
    """LLM 기반 평가를 수행하는 클래스"""
    
    def __init__(self):
        """LLM 평가자 초기화"""
        self.llm = NovaLiteLLM()
        self.config = ChainUtils.get_llm_config()
    
    def evaluate(self, project_info: str, system_prompt: str, user_prompt: str, 
                project_type: str = "balanced") -> Dict[str, Any]:
        """
        LLM을 사용하여 평가를 수행합니다.
        
        Args:
            project_info: 프로젝트 정보
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            project_type: 프로젝트 타입
            
        Returns:
            Dict: 평가 결과
        """
        try:
            # NovaLiteLLM 호출
            response = self.llm.invoke(
                user_message=user_prompt,
                system_message=system_prompt,
                temperature=self.config['temperature'],
                max_tokens=self.config['max_tokens']
            )
            
            # 응답 파싱 및 구조화
            return ChainUtils.parse_llm_response(response, project_type)
            
        except Exception as e:
            print(f"LLM 호출 중 오류 발생: {e}")
            return ChainUtils.handle_llm_error(e, project_type)