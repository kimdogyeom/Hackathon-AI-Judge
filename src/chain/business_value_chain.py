import yaml
import json
from typing import Optional, Any, Dict

from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.runnables.utils import Input, Output

from src.llm.nova_lite_llm import NovaLiteLLM


# -*- coding: utf-8 -*-
class BusinessValueChain(Runnable):
    """
    비즈니스 가치 체인.
    NovaLiteLLM을 사용하여 프로젝트의 비즈니스적 가치를 평가합니다.
    """

    def __init__(self, config_path: str = "src/config/evaluation.yaml"):
        super().__init__()
        self._load_evaluation_criteria(config_path)
        self.llm = NovaLiteLLM()

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
            input: 평가할 프로젝트 정보 (문자열 또는 딕셔너리)
            config: 실행 설정 (선택)
            **kwargs: 추가 파라미터
            
        Returns:
            Dict: 구조화된 평가 결과 (점수 포함)
        """
        try:
            # 입력 데이터 처리
            project_info = self._process_input(input)
            
            # NovaLiteLLM을 사용하여 비즈니스 가치 평가 수행
            evaluation_result = self._evaluate_business_value(project_info)
            
            return evaluation_result
            
        except Exception as e:
            print(f"비즈니스 가치 평가 중 오류 발생: {e}")
            return {
                "error": str(e),
                "total_score": 0,
                "pain_killer_score": 0,
                "vitamin_score": 0,
                "evaluation_type": "error"
            }

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

    def _evaluate_business_value(self, project_info: str) -> Dict[str, Any]:
        """
        NovaLiteLLM을 사용하여 비즈니스 가치를 평가합니다.
        
        Args:
            project_info: 평가할 프로젝트 정보
            
        Returns:
            Dict: 구조화된 평가 결과
        """
        # 시스템 프롬프트 구성
        system_message = self._build_system_prompt()
        
        # 사용자 메시지 구성
        user_message = self._build_user_prompt(project_info)
        
        try:
            # NovaLiteLLM 호출
            response = self.llm.invoke(
                user_message=user_message,
                system_message=system_message,
                temperature=0.3,  # 일관된 평가를 위해 낮은 temperature 사용
                max_tokens=3000
            )
            
            # 응답 파싱 및 구조화
            return self._parse_evaluation_response(response)
            
        except Exception as e:
            print(f"LLM 호출 중 오류 발생: {e}")
            return {
                "error": f"LLM 호출 실패: {str(e)}",
                "total_score": 0,
                "pain_killer_score": 0,
                "vitamin_score": 0,
                "evaluation_type": "error"
            }

    def _build_system_prompt(self) -> str:
        """
        비즈니스 가치 평가를 위한 시스템 프롬프트를 구성합니다.
        
        Returns:
            str: 시스템 프롬프트
        """
        pain_killer_criteria = "\n".join([f"- {criteria}" for criteria in self.pain_killer_evaluation_list])
        vitamin_criteria = "\n".join([f"- {criteria}" for criteria in self.vitamin_evaluation_list])
        
        return f"""당신은 비즈니스 가치 평가 전문가입니다. 주어진 프로젝트의 비즈니스적 가치를 Pain Killer와 Vitamin 관점에서 평가해주세요.

평가 기준:

**Pain Killer 기준 (필수적 문제 해결):**
{pain_killer_criteria}

**Vitamin 기준 (부가적 가치 제공):**
{vitamin_criteria}

평가 방법:
1. 각 기준에 대해 1-10점으로 평가
2. Pain Killer와 Vitamin 각각의 평균 점수 계산
3. 전체 점수는 (Pain Killer 점수 × 0.6) + (Vitamin 점수 × 0.4)로 계산
4. 주요 평가 유형 결정 (pain_killer_dominant, vitamin_dominant, balanced)

**중요: 응답은 반드시 아래 JSON 형식만으로 제공해주세요. 다른 설명이나 텍스트는 포함하지 마세요.**

```json
{{
    "pain_killer_score": 숫자,
    "vitamin_score": 숫자,
    "total_score": 숫자,
    "evaluation_type": "pain_killer_dominant|vitamin_dominant|balanced",
    "reasoning": "평가 근거 설명",
    "key_strengths": ["강점1", "강점2", "강점3"],
    "improvement_areas": ["개선점1", "개선점2"]
}}
```"""

    def _build_user_prompt(self, project_info: str) -> str:
        """
        사용자 프롬프트를 구성합니다.
        
        Args:
            project_info: 프로젝트 정보
            
        Returns:
            str: 사용자 프롬프트
        """
        return f"""다음 프로젝트의 비즈니스 가치를 평가해주세요:

{project_info}

위의 평가 기준에 따라 Pain Killer와 Vitamin 관점에서 종합적으로 분석하고, 반드시 JSON 형식으로만 응답해주세요. 다른 설명은 포함하지 마세요."""

    def _parse_evaluation_response(self, response: str) -> Dict[str, Any]:
        """
        LLM 응답을 파싱하여 구조화된 결과로 변환합니다.
        
        Args:
            response: LLM 응답
            
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
                result.setdefault("pain_killer_score", 0)
                result.setdefault("vitamin_score", 0)
                result.setdefault("total_score", 0)
                result.setdefault("evaluation_type", "unknown")
                result.setdefault("reasoning", "")
                result.setdefault("key_strengths", [])
                result.setdefault("improvement_areas", [])
                
                # 점수 유효성 검증
                result["pain_killer_score"] = max(0, min(10, float(result["pain_killer_score"])))
                result["vitamin_score"] = max(0, min(10, float(result["vitamin_score"])))
                result["total_score"] = max(0, min(10, float(result["total_score"])))
                
                return result
            else:
                # JSON 형식이 아닌 경우 기본 파싱 시도
                return self._fallback_parse(response)
                
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"응답 파싱 실패: {e}")
            return self._fallback_parse(response)

    def _fallback_parse(self, response: str) -> Dict[str, Any]:
        """
        JSON 파싱 실패 시 대체 파싱 방법을 사용합니다.
        
        Args:
            response: LLM 응답
            
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
            "pain_killer_score": avg_score,
            "vitamin_score": avg_score,
            "total_score": avg_score,
            "evaluation_type": "fallback_parsed",
            "reasoning": response[:500] + "..." if len(response) > 500 else response,
            "key_strengths": ["응답 파싱 실패로 인한 기본값"],
            "improvement_areas": ["구조화된 응답 형식 개선 필요"]
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

