# -*- coding: utf-8 -*-
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import re
import yaml
from typing import Dict, Any, List
from .base_evaluation_chain import EvaluationChainBase


class InnovationChain(EvaluationChainBase):
    """
    혁신성 체인.
    프로젝트의 아이디어의 독창성과 혁신성을 평가합니다.
    
    기술적 참신성과 창의성을 종합적으로 분석하여 점수, 근거, 개선 제안을 제공합니다.
    """

    def __init__(self, llm=None, config_path: str = "src/config/evaluation.yaml"):
        super().__init__("InnovationChain")
        if llm is None:
            from src.llm.nova_lite_llm import NovaLiteLLM
            self.llm = NovaLiteLLM()
        else:
            self.llm = llm
        self.output_parser = StrOutputParser()
        self._load_evaluation_criteria(config_path)

    def _load_evaluation_criteria(self, config_path: str):
        """evaluation.yaml에서 Innovation 평가 기준을 로드합니다."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                criteria = yaml.safe_load(file)
            
            innovation = criteria.get('Innovation', {})
            self.pain_killer_criteria = innovation.get('pain_killer', [])
            self.vitamin_criteria = innovation.get('vitamin', [])
            
        except Exception as e:
            self.logger.warning(f"평가 기준 로드 실패, 기본값 사용: {e}")
            self.pain_killer_criteria = [
                "기존에 없는 문제를 정의/해결하는가?",
                "경쟁 솔루션 대비 필수적인 차별화가 있는가?"
            ]
            self.vitamin_criteria = [
                "기존 방식을 개선하는가?",
                "창의적이고 독창적인 접근을 보여주는가?"
            ]

    def _build_prompt_template(self):
        """evaluation.yaml 기준을 활용한 프롬프트 템플릿을 구성합니다."""
        pain_killer_criteria = "\n".join([f"- {criteria}" for criteria in self.pain_killer_criteria])
        vitamin_criteria = "\n".join([f"- {criteria}" for criteria in self.vitamin_criteria])
        
        return ChatPromptTemplate.from_template(f"""
        ## 평가 대상: 해커톤 프로젝트 혁신성 평가

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

        ## 혁신성 평가 기준 (Innovation 관점):

        **Pain Killer 기준 (필수적 혁신):**
        {pain_killer_criteria}

        **Vitamin 기준 (부가적 혁신):**
        {vitamin_criteria}

        ## 평가 수행:
        위 기준들을 적용하여 {{classification}} 특성을 고려한 혁신성 평가를 수행해주세요.
        다음 형식으로 JSON 응답을 제공해주세요:
        ```json
        {{{{
            "score": [0-10 사이의 점수],
            "reasoning": "[평가 근거 설명 - 위 기준들을 적용한 혁신성 분석]",
            "suggestions": ["[개선 제안1]", "[개선 제안2]", "[개선 제안3]"],
            "strengths": ["[혁신적 강점1]", "[혁신적 강점2]"],
            "weaknesses": ["[혁신성 부족 요소1]", "[혁신성 부족 요소2]"],
            "innovation_aspects": {{{{
                "pain_killer_score": [0-10],
                "vitamin_score": [0-10],
                "idea_originality": [0-10],
                "technical_novelty": [0-10],
                "market_innovation": [0-10]
            }}}}
        }}}}
        ```

        결과는 반드시 유효한 JSON 형식이어야 합니다. 다른 텍스트는 포함하지 마세요.
        """)

    def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        실제 혁신성 분석 로직을 수행합니다.
        
        Args:
            data: 전처리된 입력 데이터
            
        Returns:
            Dict: 혁신성 분석 결과
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
            self.logger.error(f"혁신성 분석 중 오류 발생: {str(e)}")
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
            "reasoning": result.get("reasoning", "혁신성 평가가 완료되었습니다."),
            "suggestions": result.get("suggestions", result.get("improvement_suggestions", [])),
            "strengths": result.get("strengths", []),
            "weaknesses": result.get("weaknesses", []),
            "innovation_aspects": result.get("innovation_aspects", {})
        }
        
        # suggestions가 리스트가 아닌 경우 변환
        if not isinstance(normalized_result["suggestions"], list):
            normalized_result["suggestions"] = [str(normalized_result["suggestions"])]
        
        # 빈 suggestions인 경우 기본값 제공
        if not normalized_result["suggestions"]:
            normalized_result["suggestions"] = [
                "더 구체적인 혁신 요소를 명시하여 차별화 강화",
                "기술적 참신성을 높이기 위한 추가 연구 개발",
                "시장에서의 혁신적 가치 제안 명확화"
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
            "reasoning": "혁신성 평가를 완료할 수 없어 기본 점수를 제공합니다. 추가 정보가 필요합니다.",
            "suggestions": [
                "프로젝트의 혁신적 요소를 더 구체적으로 설명",
                "기술적 참신성과 창의성을 명확히 제시",
                "기존 솔루션과의 차별점 강조"
            ],
            "strengths": ["평가 정보 부족"],
            "weaknesses": ["혁신성 평가를 위한 충분한 정보 부족"],
            "innovation_aspects": {
                "idea_originality": 5.0,
                "technical_novelty": 5.0,
                "creative_approach": 5.0,
                "market_innovation": 5.0,
                "value_creation": 5.0
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
        # invoke 메서드를 통해 표준화된 처리 수행
        return self.invoke(data)

    def as_runnable(self):
        """
        해당 클래스를 LangChain Runnable로 변환
        """
        return self