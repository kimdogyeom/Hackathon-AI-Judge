# -*- coding: utf-8 -*-
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import re
import yaml
from typing import Dict, Any, List
from .base_evaluation_chain import EvaluationChainBase


class CostAnalysisChain(EvaluationChainBase):
    """
    비용 분석 체인.
    프로젝트의 비용 효율성과 ROI를 평가합니다.
    
    evaluation.yaml의 BusinessValue 기준을 활용하여 비용 관점에서 평가합니다.
    """

    def __init__(self, llm=None, config_path: str = "src/config/evaluation.yaml"):
        super().__init__("CostAnalysisChain")
        if llm is None:
            from src.llm.nova_lite_llm import NovaLiteLLM
            self.llm = NovaLiteLLM()
        else:
            self.llm = llm
        self.output_parser = StrOutputParser()
        self._load_evaluation_criteria(config_path)

    def _load_evaluation_criteria(self, config_path: str):
        """evaluation.yaml에서 BusinessValue 평가 기준을 로드합니다."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                criteria = yaml.safe_load(file)
            
            business_value = criteria.get('BusinessValue', {})
            self.pain_killer_criteria = business_value.get('pain_killer', [])
            self.vitamin_criteria = business_value.get('vitamin', [])
            
        except Exception as e:
            self.logger.warning(f"평가 기준 로드 실패, 기본값 사용: {e}")
            self.pain_killer_criteria = [
                "비용 문제가 타겟 고객의 생존 또는 운영 손실과 직결되는가?",
                "기존 해결책의 한계가 심각한가?",
                "즉각적인 비용 절감이 필요한가?"
            ]
            self.vitamin_criteria = [
                "비용 절감이 편의성 및 효율성을 개선해주는가?",
                "프리미엄의 가치를 제공하는가?",
                "기존 대안보다 차별화를 보여주는가?"
            ]

    def _build_prompt_template(self):
        """evaluation.yaml 기준을 활용한 프롬프트 템플릿을 구성합니다."""
        pain_killer_criteria = "\n".join([f"- {criteria}" for criteria in self.pain_killer_criteria])
        vitamin_criteria = "\n".join([f"- {criteria}" for criteria in self.vitamin_criteria])
        
        return ChatPromptTemplate.from_template(f"""
        ## 평가 대상: 해커톤 프로젝트 비용 효율성 평가

        ### 프로젝트 정보:
        - 프로젝트명: {{project_name}}
        - 설명: {{description}}
        - 기술: {{technology}}
        - 타겟 사용자: {{target_users}}
        - 비즈니스 모델: {{business_model}}

        ### 분류:
        - 이 프로젝트는 {{classification}} 유형으로 분류되었습니다.

        ### 종합 분석:
        {{material_analysis}}

        ### 데이터 제한사항:
        {{data_limitations}}

        ## 비용 효율성 평가 기준 (BusinessValue 관점):

        **Pain Killer 기준 (필수적 비용 문제 해결):**
        {pain_killer_criteria}

        **Vitamin 기준 (부가적 비용 가치 제공):**
        {vitamin_criteria}

        ## 평가 수행:
        위 기준들을 비용 효율성 관점에서 적용하여 {{classification}} 특성을 고려한 평가를 수행해주세요.
        다음 형식으로 JSON 응답을 제공해주세요:
        ```json
        {{{{
            "score": [0-10 사이의 점수],
            "reasoning": "[평가 근거 설명 - 위 기준들을 비용 관점에서 적용한 분석]",
            "suggestions": ["[개선 제안1]", "[개선 제안2]", "[개선 제안3]"],
            "cost_breakdown": {{{{
                "development_cost": "[개발 비용 분석]",
                "operational_cost": "[운영 비용 분석]", 
                "expected_revenue": "[예상 수익 분석]",
                "roi_estimate": "[ROI 추정치]"
            }}}},
            "strengths": ["[비용 효율성 강점1]", "[비용 효율성 강점2]"],
            "risks": ["[비용 리스크1]", "[비용 리스크2]"],
            "cost_aspects": {{{{
                "pain_killer_score": [0-10],
                "vitamin_score": [0-10],
                "development_efficiency": [0-10],
                "operational_efficiency": [0-10],
                "roi_potential": [0-10]
            }}}}
        }}}}
        ```

        결과는 반드시 유효한 JSON 형식이어야 합니다. 다른 텍스트는 포함하지 마세요.
        """)

    def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        실제 비용 효율성 분석 로직을 수행합니다.
        
        Args:
            data: 전처리된 입력 데이터
            
        Returns:
            Dict: 비용 분석 결과
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
        prompt_template = self._build_prompt_template()
        prompt = prompt_template.format(
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
            self.logger.error(f"비용 분석 중 오류 발생: {str(e)}")
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
            "reasoning": result.get("reasoning", "비용 효율성 평가가 완료되었습니다."),
            "suggestions": result.get("suggestions", []),
            "cost_breakdown": result.get("cost_breakdown", {}),
            "strengths": result.get("strengths", []),
            "risks": result.get("risks", []),
            "cost_aspects": result.get("cost_aspects", {})
        }
        
        # suggestions가 리스트가 아닌 경우 변환
        if not isinstance(normalized_result["suggestions"], list):
            normalized_result["suggestions"] = [str(normalized_result["suggestions"])]
        
        # 빈 suggestions인 경우 기본값 제공
        if not normalized_result["suggestions"]:
            normalized_result["suggestions"] = [
                "개발 비용 최적화를 위한 기술 스택 재검토",
                "운영 비용 절감을 위한 클라우드 서비스 활용",
                "수익 모델 다각화를 통한 ROI 개선"
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
            "reasoning": "비용 효율성 평가를 완료할 수 없어 기본 점수를 제공합니다. 추가 정보가 필요합니다.",
            "suggestions": [
                "구체적인 개발 비용 계획 수립",
                "운영 비용 예측 및 최적화 방안 마련",
                "명확한 수익 모델과 ROI 계산"
            ],
            "cost_breakdown": {
                "development_cost": "정보 부족으로 분석 불가",
                "operational_cost": "정보 부족으로 분석 불가",
                "expected_revenue": "정보 부족으로 분석 불가",
                "roi_estimate": "정보 부족으로 계산 불가"
            },
            "strengths": ["평가 정보 부족"],
            "risks": ["비용 분석을 위한 충분한 정보 부족"],
            "cost_aspects": {
                "development_efficiency": 5.0,
                "operational_efficiency": 5.0,
                "revenue_potential": 5.0,
                "cost_optimization": 5.0,
                "sustainability": 5.0
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