# -*- coding: utf-8 -*-
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import re
import yaml
from typing import Dict, Any, List
from .base_evaluation_chain import EvaluationChainBase


class SustainabilityChain(EvaluationChainBase):
    """
    지속가능성 체인.
    프로젝트의 환경적, 경제적, 사회적 지속가능성을 평가합니다.
    
    ESG(Environmental, Social, Governance) 관점에서 장기적 지속가능성을 종합적으로 분석합니다.
    """

    def __init__(self, llm=None, config_path: str = "src/config/evaluation.yaml"):
        super().__init__("SustainabilityChain")
        if llm is None:
            from src.llm.nova_lite_llm import NovaLiteLLM
            self.llm = NovaLiteLLM()
        else:
            self.llm = llm
        self.output_parser = StrOutputParser()
        self._load_evaluation_criteria(config_path)

    def _load_evaluation_criteria(self, config_path: str):
        """evaluation.yaml에서 Sustainability 평가 기준을 로드합니다."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                criteria = yaml.safe_load(file)
            
            sustainability = criteria.get('Sustainability', {})
            self.pain_killer_criteria = sustainability.get('pain_killer', [])
            self.vitamin_criteria = sustainability.get('vitamin', [])
            
        except Exception as e:
            self.logger.warning(f"평가 기준 로드 실패, 기본값 사용: {e}")
            self.pain_killer_criteria = [
                "환경/사회 지속가능성 문제를 해결할 수 있는가?",
                "기존 방식의 환경 피해가 심각한가?"
            ]
            self.vitamin_criteria = [
                "장기적인 환경적 가치를 제공하는가?",
                "지속가능한 소비 문화 조성에 기여하는가?"
            ]

        # 지속가능성 평가 프롬프트 템플릿
        self.prompt_template = ChatPromptTemplate.from_template("""
        ## 평가 대상: 해커톤 프로젝트 지속가능성 평가

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

        ## 지속가능성 평가 지침 (ESG 관점):
        1. **환경적 지속가능성 (Environmental)**: 
           - 환경 보호와 자원 효율성
           - 탄소 발자국 및 에너지 효율성
           - 순환경제와 폐기물 감소
        2. **사회적 지속가능성 (Social)**:
           - 사회적 책임과 윤리적 운영
           - 이해관계자와의 상생
           - 인권과 노동 환경 고려
        3. **경제적 지속가능성**:
           - 장기적 수익성과 성장 가능성
           - 리스크 관리와 재무 안정성
           - 혁신을 통한 경쟁력 유지
        4. **거버넌스 (Governance)**:
           - 투명한 의사결정 구조
           - 윤리적 경영과 컴플라이언스
           - 지속가능한 운영 체계

        ## 분류별 평가 기준:
        - **PainKiller 관점**: 문제 해결의 지속가능성과 장기적 효과성에 중점
        - **Vitamin 관점**: 가치 창출의 지속가능성과 사회적 책임에 중점
        - **Balanced 관점**: 환경, 사회, 경제적 지속가능성의 균형적 평가

        ## 평가 수행:
        {classification} 특성을 고려하여 이 프로젝트의 지속가능성을 0-10점 척도로 평가해주세요.
        다음 형식으로 JSON 응답을 제공해주세요:
        ```json
        {{
            "score": [0-10 사이의 점수],
            "reasoning": "[평가 근거 설명 - 구체적인 지속가능성 분석과 ESG 요소]",
            "suggestions": ["[개선 제안1]", "[개선 제안2]", "[개선 제안3]"],
            "sustainability_analysis": {{
                "environmental": "[환경적 지속가능성 분석]",
                "social": "[사회적 지속가능성 분석]",
                "economic": "[경제적 지속가능성 분석]",
                "governance": "[거버넌스 분석]"
            }},
            "esg_strengths": ["[ESG 강점1]", "[ESG 강점2]"],
            "sustainability_risks": ["[지속가능성 리스크1]", "[지속가능성 리스크2]"],
            "sustainability_aspects": {{
                "environmental_impact": [0-10],
                "social_responsibility": [0-10],
                "economic_viability": [0-10],
                "governance_quality": [0-10],
                "long_term_sustainability": [0-10]
            }}
        }}
        ```

        결과는 반드시 유효한 JSON 형식이어야 합니다. 다른 텍스트는 포함하지 마세요.
        """)

    def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        실제 지속가능성 분석 로직을 수행합니다.
        
        Args:
            data: 전처리된 입력 데이터
            
        Returns:
            Dict: 지속가능성 분석 결과
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
            self.logger.error(f"지속가능성 분석 중 오류 발생: {str(e)}")
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
            "reasoning": result.get("reasoning", "지속가능성 평가가 완료되었습니다."),
            "suggestions": result.get("suggestions", []),
            "sustainability_analysis": result.get("sustainability_analysis", {}),
            "esg_strengths": result.get("esg_strengths", []),
            "sustainability_risks": result.get("sustainability_risks", []),
            "sustainability_aspects": result.get("sustainability_aspects", {})
        }
        
        # suggestions가 리스트가 아닌 경우 변환
        if not isinstance(normalized_result["suggestions"], list):
            normalized_result["suggestions"] = [str(normalized_result["suggestions"])]
        
        # 빈 suggestions인 경우 기본값 제공
        if not normalized_result["suggestions"]:
            normalized_result["suggestions"] = [
                "환경 영향 최소화를 위한 친환경 기술 도입",
                "사회적 책임을 고려한 윤리적 운영 체계 구축",
                "장기적 수익성 확보를 위한 지속가능한 비즈니스 모델 개발"
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
            "reasoning": "지속가능성 평가를 완료할 수 없어 기본 점수를 제공합니다. 추가 정보가 필요합니다.",
            "suggestions": [
                "ESG 관점에서 환경, 사회, 거버넌스 요소 고려",
                "장기적 지속가능성을 위한 전략 수립",
                "이해관계자와의 상생 방안 마련"
            ],
            "sustainability_analysis": {
                "environmental": "정보 부족으로 분석 불가",
                "social": "정보 부족으로 분석 불가",
                "economic": "정보 부족으로 분석 불가",
                "governance": "정보 부족으로 분석 불가"
            },
            "esg_strengths": ["평가 정보 부족"],
            "sustainability_risks": ["지속가능성 분석을 위한 충분한 정보 부족"],
            "sustainability_aspects": {
                "environmental_impact": 5.0,
                "social_responsibility": 5.0,
                "economic_viability": 5.0,
                "governance_quality": 5.0,
                "long_term_sustainability": 5.0
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