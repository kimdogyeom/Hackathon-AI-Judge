# -*- coding: utf-8 -*-
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import re
import yaml
from typing import Dict, Any, List
from .base_evaluation_chain import EvaluationChainBase


class TechnicalFeasibilityChain(EvaluationChainBase):
    """
    기술적 실현가능성 체인.
    프로젝트의 기술적 복잡도와 구현 가능성을 평가합니다.
    
    기술 스택, 개발 난이도, 인프라 요구사항, 확장성 등을 종합적으로 분석합니다.
    """

    def __init__(self, llm=None, config_path: str = "src/config/evaluation.yaml"):
        super().__init__("TechnicalFeasibilityChain")
        if llm is None:
            from src.llm.nova_lite_llm import NovaLiteLLM
            self.llm = NovaLiteLLM()
        else:
            self.llm = llm
        self.output_parser = StrOutputParser()
        self._load_evaluation_criteria(config_path)

    def _load_evaluation_criteria(self, config_path: str):
        """evaluation.yaml에서 TechnicalFeasibility 평가 기준을 로드합니다."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                criteria = yaml.safe_load(file)
            
            technical_feasibility = criteria.get('TechnicalFeasibility', {})
            self.pain_killer_criteria = technical_feasibility.get('pain_killer', [])
            self.vitamin_criteria = technical_feasibility.get('vitamin', [])
            
        except Exception as e:
            self.logger.warning(f"평가 기준 로드 실패, 기본값 사용: {e}")
            self.pain_killer_criteria = [
                "기술이 필수적인 문제(생존/경쟁력 직결)를 해결하는가?",
                "기존 기술적 해결책의 한계가 심각한가?"
            ]
            self.vitamin_criteria = [
                "차별화된 경험을 제공하는가?",
                "사용자 편의성을 기술적으로 개선하는가?"
            ]

        # 기술적 실현가능성 평가 프롬프트 템플릿
        self.prompt_template = ChatPromptTemplate.from_template("""
        ## 평가 대상: 해커톤 프로젝트 기술적 실현가능성 평가

        ### 프로젝트 정보:
        - 프로젝트명: {project_name}
        - 설명: {description}
        - 기술: {technology}
        - 타겟 사용자: {target_users}
        - 비즈니스 모델: {business_model}

        ### 분류:
        - 이 프로젝트는 {classification} 유형으로 분류되었습니다.

        ### 종합 분석:
        {material_analysis}

        ### 데이터 제한사항:
        {data_limitations}

        ## 기술적 실현가능성 평가 지침:
        1. **기술 스택 적합성**: 선택된 기술들의 적합성과 성숙도
        2. **개발 복잡도**: 구현에 필요한 기술적 난이도와 개발 시간
        3. **인프라 요구사항**: 필요한 서버, 데이터베이스, 외부 서비스 등
        4. **확장성과 성능**: 사용자 증가에 따른 시스템 확장 가능성
        5. **기술적 리스크**: 구현 과정에서 발생할 수 있는 기술적 위험 요소

        ## 분류별 평가 기준:
        - **PainKiller 관점**: 문제 해결을 위한 기술적 안정성과 신뢰성에 중점
        - **Vitamin 관점**: 사용자 경험 향상을 위한 기술적 혁신성과 성능에 중점
        - **Balanced 관점**: 안정성과 혁신성의 균형적 기술적 실현가능성

        ## 평가 수행:
        {classification} 특성을 고려하여 이 프로젝트의 기술적 실현가능성을 0-10점 척도로 평가해주세요.
        다음 형식으로 JSON 응답을 제공해주세요:
        ```json
        {{
            "score": [0-10 사이의 점수],
            "reasoning": "[평가 근거 설명 - 구체적인 기술적 분석과 실현가능성 평가]",
            "suggestions": ["[개선 제안1]", "[개선 제안2]", "[개선 제안3]"],
            "technical_analysis": {{
                "technology_stack": "[기술 스택 분석]",
                "development_complexity": "[개발 복잡도 분석]",
                "infrastructure_requirements": "[인프라 요구사항 분석]",
                "scalability_assessment": "[확장성 평가]"
            }},
            "technical_strengths": ["[기술적 강점1]", "[기술적 강점2]"],
            "technical_risks": ["[기술적 리스크1]", "[기술적 리스크2]"],
            "feasibility_aspects": {{
                "technology_maturity": [0-10],
                "development_complexity": [0-10],
                "infrastructure_feasibility": [0-10],
                "scalability_potential": [0-10],
                "technical_risk_level": [0-10]
            }}
        }}
        ```

        결과는 반드시 유효한 JSON 형식이어야 합니다. 다른 텍스트는 포함하지 마세요.
        """)

    def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        실제 기술적 실현가능성 분석 로직을 수행합니다.
        
        Args:
            data: 전처리된 입력 데이터
            
        Returns:
            Dict: 기술적 실현가능성 분석 결과
        """
        # 데이터 제한사항 확인
        limitations = self._check_data_availability(data)
        
        # 필요한 데이터 추출
        parsed_data = data.get("parsed_data", {})
        classification = data.get("classification", "balanced")
        material_analysis = data.get("material_analysis", "")
        
        # 데이터 제한사항 메시지 생성
        limitations_text = ""
        if limitations:
            limitations_text = "다음 제한사항이 있습니다: " + ", ".join(limitations)
        else:
            limitations_text = "모든 자료가 충분히 제공되었습니다."

        # 프롬프트 구성
        prompt = self.prompt_template.format(
            project_name=parsed_data.get("project_name", "정보 없음"),
            description=parsed_data.get("description", "정보 없음"),
            technology=parsed_data.get("technology", "정보 없음"),
            target_users=parsed_data.get("target_users", "정보 없음"),
            business_model=parsed_data.get("business_model", "정보 없음"),
            classification=classification,
            material_analysis=material_analysis or "종합 분석 정보가 제공되지 않았습니다.",
            data_limitations=limitations_text
        )

        try:
            # LLM 호출
            response = self.llm.invoke(prompt)
            result_text = self.output_parser.invoke(response)

            # JSON 파싱
            result = self._parse_llm_response(result_text)
            
            # 데이터 제한사항이 있는 경우 결과에 추가
            if limitations:
                result["data_limitations"] = "; ".join(limitations)
            
            return result

        except Exception as e:
            self.logger.error(f"기술적 실현가능성 분석 중 오류 발생: {str(e)}")
            return self._get_fallback_result(limitations)
    
    def _parse_llm_response(self, result_text: str) -> Dict[str, Any]:
        """
        LLM 응답을 파싱하여 구조화된 결과로 변환합니다.
        
        Args:
            result_text: LLM 응답 텍스트
            
        Returns:
            Dict: 파싱된 결과
        """
        try:
            # JSON 부분만 추출
            json_match = re.search(r'\{\s*"score".*\}', result_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
            else:
                # 전체 텍스트를 JSON으로 파싱 시도
                result = json.loads(result_text)
            
            # 결과 검증 및 정규화
            return self._validate_and_normalize_result(result)

        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON 파싱 실패: {str(e)}")
            return self._get_fallback_result()
    
    def _validate_and_normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        분석 결과를 검증하고 정규화합니다.
        
        Args:
            result: 원본 분석 결과
            
        Returns:
            Dict: 검증 및 정규화된 결과
        """
        # 필수 필드 확인 및 기본값 설정
        normalized_result = {
            "score": self._validate_score(result.get("score", 0)),
            "reasoning": result.get("reasoning", "기술적 실현가능성 평가가 완료되었습니다."),
            "suggestions": result.get("suggestions", []),
            "technical_analysis": result.get("technical_analysis", {}),
            "technical_strengths": result.get("technical_strengths", []),
            "technical_risks": result.get("technical_risks", []),
            "feasibility_aspects": result.get("feasibility_aspects", {})
        }
        
        # suggestions가 리스트가 아닌 경우 변환
        if not isinstance(normalized_result["suggestions"], list):
            normalized_result["suggestions"] = [str(normalized_result["suggestions"])]
        
        # 빈 suggestions인 경우 기본값 제공
        if not normalized_result["suggestions"]:
            normalized_result["suggestions"] = [
                "검증된 기술 스택 사용으로 개발 리스크 최소화",
                "단계적 개발 접근법으로 복잡도 관리",
                "확장 가능한 아키텍처 설계로 성장 대비"
            ]
        
        return normalized_result
    
    def _validate_score(self, score: Any) -> float:
        """
        점수를 검증하고 유효한 범위로 조정합니다.
        
        Args:
            score: 원본 점수
            
        Returns:
            float: 검증된 점수 (0.0-10.0)
        """
        try:
            score_float = float(score)
            return max(0.0, min(10.0, score_float))
        except (ValueError, TypeError):
            self.logger.warning(f"유효하지 않은 점수 값: {score}, 기본값 5.0 사용")
            return 5.0
    
    def _get_fallback_result(self, limitations: List[str] = None) -> Dict[str, Any]:
        """
        오류 상황에서 사용할 기본 결과를 반환합니다.
        
        Args:
            limitations: 데이터 제한사항 목록
            
        Returns:
            Dict: 기본 결과
        """
        result = {
            "score": 5.0,
            "reasoning": "기술적 실현가능성 평가를 완료할 수 없어 기본 점수를 제공합니다. 추가 정보가 필요합니다.",
            "suggestions": [
                "구체적인 기술 스택과 아키텍처 명시",
                "개발 일정과 리소스 계획 수립",
                "기술적 리스크 분석 및 대응 방안 마련"
            ],
            "technical_analysis": {
                "technology_stack": "정보 부족으로 분석 불가",
                "development_complexity": "정보 부족으로 분석 불가",
                "infrastructure_requirements": "정보 부족으로 분석 불가",
                "scalability_assessment": "정보 부족으로 분석 불가"
            },
            "technical_strengths": ["평가 정보 부족"],
            "technical_risks": ["기술적 실현가능성 분석을 위한 충분한 정보 부족"],
            "feasibility_aspects": {
                "technology_maturity": 5.0,
                "development_complexity": 5.0,
                "infrastructure_feasibility": 5.0,
                "scalability_potential": 5.0,
                "technical_risk_level": 5.0
            }
        }
        
        if limitations:
            result["data_limitations"] = "; ".join(limitations)
        
        return result

    def __call__(self, data):
        """
        기존 호환성을 위한 __call__ 메서드.
        
        Args:
            data: 평가 데이터
            
        Returns:
            Dict: 평가 결과
        """
        return self.invoke(data)

    def as_runnable(self):
        """
        해당 클래스를 LangChain Runnable로 변환
        """
        return self