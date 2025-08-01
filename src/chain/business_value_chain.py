import yaml
import json
from typing import Optional, Any, Dict

from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.runnables.utils import Input, Output

from src.llm.nova_lite_llm import NovaLiteLLM
from src.config.config_manager import get_config_manager


# -*- coding: utf-8 -*-
class BusinessValueChain(Runnable):
    """
    비즈니스 가치 체인.
    NovaLiteLLM을 사용하여 프로젝트의 비즈니스적 가치를 평가합니다.
    """

    def __init__(self, config_path: str = "src/config/settings/evaluation/evaluation.yaml"):
        super().__init__()
        self._load_evaluation_criteria(config_path)
        self.llm = NovaLiteLLM()
        self.config_manager = get_config_manager()

    def _load_evaluation_criteria(self, config_path: str):
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                criteria = yaml.safe_load(file)

            business_value = criteria['BusinessValue']
            self.pain_killer_evaluation_list = business_value['pain_killer']
            self.vitamin_evaluation_list = business_value['vitamin']

        except Exception as e:
            print(f"YAML 로드 실패, 기본값 사용: {e}")
            raise FileNotFoundError(e)


    def invoke(self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Output:
        """
        비즈니스 가치 평가를 실행합니다.
        
        Args:
            input: 평가할 프로젝트 정보 (딕셔너리 형태, project_type 포함)
            config: 실행 설정 (선택)
            **kwargs: 추가 파라미터
            
        Returns:
            Dict: 구조화된 평가 결과 (점수 포함)
        """
        try:
            # 입력 데이터에서 프로젝트 타입 추출
            project_type = "balanced"  # 기본값
            if isinstance(input, dict):
                project_type = input.get('project_type', 'balanced')
                if 'classification' in input and isinstance(input['classification'], dict):
                    project_type = input['classification'].get('project_type', 'balanced')
            
            # 입력 데이터 처리
            project_info = self._process_input(input)
            
            # NovaLiteLLM을 사용하여 비즈니스 가치 평가 수행
            evaluation_result = self._evaluate_business_value(project_info, project_type)
            
            return evaluation_result
            
        except Exception as e:
            print(f"비즈니스 가치 평가 중 오류 발생: {e}")
            return {
                "error": str(e),
                "score": 0,
                "reasoning": f"비즈니스 가치 평가 중 오류 발생: {str(e)}",
                "suggestions": ["시스템 관리자에게 문의하세요"],
                "evaluation_type": "error"
            }


    def _evaluate_business_value(self, project_info: str, project_type: str = "balanced") -> Dict[str, Any]:
        """
        NovaLiteLLM을 사용하여 비즈니스 가치를 평가합니다.
        
        Args:
            project_info: 평가할 프로젝트 정보
            project_type: 이미 분류된 프로젝트 타입 (painkiller/vitamin/balanced)
            
        Returns:
            Dict: 구조화된 평가 결과
        """
        # 시스템 프롬프트 구성 (프로젝트 타입 반영)
        system_message = self._build_system_prompt(project_type)
        
        # 사용자 메시지 구성
        user_message = self._build_user_prompt(project_info, project_type)
        
        try:
            # 설정에서 LLM 파라미터 로드
            temperature = self.config_manager.get_config('system_config.yaml', 'llm.temperature', 0.3)
            max_tokens = self.config_manager.get_config('system_config.yaml', 'llm.max_tokens', 3000)
            
            # NovaLiteLLM 호출
            response = self.llm.invoke(
                user_message=user_message,
                system_message=system_message,
                temperature=temperature,  # 설정에서 로드된 temperature 사용
                max_tokens=max_tokens
            )
            
            # 응답 파싱 및 구조화
            return self._parse_evaluation_response(response, project_type)
            
        except Exception as e:
            print(f"LLM 호출 중 오류 발생: {e}")
            return {
                "error": f"LLM 호출 실패: {str(e)}",
                "score": 0,
                "reasoning": f"LLM 호출 실패: {str(e)}",
                "suggestions": ["시스템 관리자에게 문의하세요"],
                "evaluation_type": "error"
            }

    def _build_system_prompt(self, project_type: str = "balanced") -> str:
        """
        비즈니스 가치 평가를 위한 시스템 프롬프트를 구성합니다.
        
        Args:
            project_type: 이미 분류된 프로젝트 타입
            
        Returns:
            str: 시스템 프롬프트
        """
        pain_killer_criteria = "\n".join([f"- {criteria}" for criteria in self.pain_killer_evaluation_list])
        vitamin_criteria = "\n".join([f"- {criteria}" for criteria in self.vitamin_evaluation_list])
        
        # 프로젝트 타입에 따른 평가 가중치 설정
        if project_type.lower() == 'painkiller':
            weight_instruction = "이 프로젝트는 PainKiller 유형으로 분류되었으므로, Pain Killer 기준에 맞춰 평가하세요."
            evaluation_criteria = pain_killer_criteria

        elif project_type.lower() == 'vitamin':
            weight_instruction = "이 프로젝트는 Vitamin 유형으로 분류되었으므로, Vitamin 기준에 맞춰 평가하세요."
            evaluation_criteria = vitamin_criteria
        else:
            weight_instruction = "이 프로젝트는 Balanced 유형으로 분류되었으므로, 두 기준을 균등하게 평가하세요."
            evaluation_criteria = pain_killer_criteria + vitamin_criteria + "평가항목에 대해서 균등하게 적용할 수 있도록 하세요"

        return f"""당신은 비즈니스 가치 평가 전문가입니다. 이미 분류된 프로젝트 유형({project_type})을 고려하여 서비스의 비즈니스적 가치를 평가해주세요.
        
        {weight_instruction}
        
        평가 기준:
        
        **평가기준:**
        {evaluation_criteria}
        
        평가 방법:
        1. 각 기준에 대해 1-10점으로 평가
        2. 프로젝트 타입에 따른 가중치 적용
        
        **중요: 응답은 반드시 아래 JSON 형식만으로 제공해주세요. 다른 설명이나 텍스트는 포함하지 마세요.**
        
        ```json
        {{
            "score": 숫자,
            "reasoning": "평가에 대한 상세한 근거를 설명, 점수에 대한 명확한 근거가 있어야 하며, 20년차 전문가가 봐도 납득할만한 이유여야 함.",
            "suggestions": ["개선점1", "개선점2", "개선점3"]
        }}
        ```"""

    def _build_user_prompt(self, project_info: str, project_type: str = "balanced") -> str:
        """
        사용자 프롬프트를 구성합니다.
        
        Args:
            project_info: 프로젝트 정보
            project_type: 이미 분류된 프로젝트 타입
            
        Returns:
            str: 사용자 프롬프트
        """
        return f"""다음 프로젝트의 비즈니스 가치를 평가해주세요:

            **프로젝트 분류**: {project_type.upper()} 유형
            **프로젝트 정보**: {project_info}
            
            이미 분류된 프로젝트 유형({project_type})을 고려하여 평가하고, 반드시 JSON 형식으로만 응답해주세요."""


    def _process_input(self, input: Input) -> str:
        """
        입력 데이터를 처리하여 문자열로 변환합니다.

        Args:
            input: 입력 데이터

        Returns:
            str: 처리된 프로젝트 정보
        """
        if isinstance(input, str):
            return input
        elif isinstance(input, dict):
            # 딕셔너리인 경우 주요 필드들을 문자열로 변환
            project_info = ""
            if "title" in input:
                project_info += f"프로젝트 제목: {input['title']}\n"
            if "description" in input:
                project_info += f"프로젝트 설명: {input['description']}\n"
            if "content" in input:
                project_info += f"내용: {input['content']}\n"
            return project_info if project_info else str(input)
        else:
            return str(input)

    def _parse_evaluation_response(self, response: str, project_type: str = "balanced") -> Dict[str, Any]:
        """
        LLM 응답을 파싱하여 구조화된 결과로 변환합니다.
        
        Args:
            response: LLM 응답
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
                result.setdefault("score", 0)
                result.setdefault("reasoning", "")
                result.setdefault("suggestions", [])
                
                # 점수 유효성 검증
                result["score"] = max(0, min(10, float(result["score"])))
                
                # 프로젝트 타입 정보 추가
                result["project_type"] = project_type
                result["evaluation_method"] = "llm_based_with_classification"
                
                return result
            else:
                # JSON 형식이 아닌 경우 기본 파싱 시도
                return self._fallback_parse(response, project_type)
                
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"응답 파싱 실패: {e}")
            return self._fallback_parse(response, project_type)


    def _fallback_parse(self, response: str, project_type: str = "balanced") -> Dict[str, Any]:
        """
        JSON 파싱 실패 시 대체 파싱 방법을 사용합니다.
        
        Args:
            response: LLM 응답
            project_type: 프로젝트 타입
            
        Returns:
            Dict: 기본 구조화된 결과
        """
        # 간단한 점수 추출 시도
        import re
        
        # 점수 패턴 찾기
        score_patterns = [
            r'점수[:\s]*(\d+(?:\.\d+)?)',
            r'score[:\s]*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)[점/점수]'
        ]
        
        scores = []
        for pattern in score_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            scores.extend([float(match) for match in matches])
        
        # 평균 점수 계산 (점수가 있는 경우)
        avg_score = sum(scores) / len(scores) if scores else 5.0
        avg_score = max(0, min(10, avg_score))
        
        return {
            "score": avg_score,
            "reasoning": response[:500] + "..." if len(response) > 500 else response,
            "suggestions": ["응답 파싱 실패로 인한 기본값", "구조화된 응답 형식 개선 필요"],
            "project_type": project_type,
            "evaluation_method": "fallback_parsed"
        }

    def run(self):
        """
        비즈니스 가치 분석을 실행하고 점수를 반환합니다.
        
        Returns:
            float: 비즈니스 가치 점수 (0-10)
        """
        # 기본 테스트용 프로젝트 정보
        test_project = "AI 기반 문서 자동 분류 시스템 개발 프로젝트"
        
        result = self.invoke(test_project)
        return result.get("total_score", 0)

