# -*- coding: utf-8 -*-
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import re
import yaml
from typing import Dict, Any, List
from .base_evaluation_chain import EvaluationChainBase


class UserEngagementChain(EvaluationChainBase):
    """
    사용자 참여도 체인.
    프로젝트의 UX/UI 품질과 사용자 만족도를 평가합니다.
    
    사용자 경험, 인터페이스 디자인, 사용성, 참여 유도 요소 등을 종합적으로 분석합니다.
    """

    def __init__(self, llm=None, config_path: str = "src/config/evaluation.yaml"):
        super().__init__("UserEngagementChain")
        if llm is None:
            from src.llm.nova_lite_llm import NovaLiteLLM
            self.llm = NovaLiteLLM()
        else:
            self.llm = llm
        self.output_parser = StrOutputParser()
        self._load_evaluation_criteria(config_path)

    def _load_evaluation_criteria(self, config_path: str):
        """evaluation.yaml에서 UserEngagement 평가 기준을 로드합니다."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                criteria = yaml.safe_load(file)
            
            user_engagement = criteria.get('UserEngagement', {})
            self.pain_killer_criteria = user_engagement.get('pain_killer', [])
            self.vitamin_criteria = user_engagement.get('vitamin', [])
            
        except Exception as e:
            self.logger.warning(f"평가 기준 로드 실패, 기본값 사용: {e}")
            self.pain_killer_criteria = [
                "감정적 고통(외로움, 스트레스 등)을 해결해주는가?",
                "기존 해결책의 한계와 접근성 문제가 심각한가?"
            ]
            self.vitamin_criteria = [
                "오락 및 재미 요소를 제공하는가?",
                "사용자 만족도와 몰입도를 높이는가?"
            ]

        # 사용자 참여도 평가 프롬프트 템플릿
        self.prompt_template = ChatPromptTemplate.from_template("""
        ## 평가 대상: 해커톤 프로젝트 사용자 참여도 평가

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

        ## 사용자 참여도 평가 지침:
        1. **사용자 경험 (UX)**: 
           - 사용자 여정과 플로우의 직관성
           - 사용 편의성과 학습 곡선
           - 사용자 니즈 충족도
        2. **사용자 인터페이스 (UI)**:
           - 시각적 디자인과 일관성
           - 반응형 디자인과 접근성
           - 인터랙션 디자인 품질
        3. **참여 유도 요소**:
           - 게임화 요소와 동기 부여
           - 개인화와 맞춤형 경험
           - 소셜 기능과 커뮤니티 요소
        4. **사용성과 만족도**:
           - 사용 편의성과 효율성
           - 오류 방지와 복구 기능
           - 전반적인 사용자 만족도

        ## 분류별 평가 기준:
        - **PainKiller 관점**: 문제 해결 과정에서의 사용 편의성과 효율성에 중점
        - **Vitamin 관점**: 사용자 경험의 즐거움과 참여 유도 요소에 중점
        - **Balanced 관점**: 실용성과 즐거움의 균형적 사용자 경험

        ## 평가 수행:
        {classification} 특성을 고려하여 이 프로젝트의 사용자 참여도를 0-10점 척도로 평가해주세요.
        다음 형식으로 JSON 응답을 제공해주세요:
        ```json
        {{
            "score": [0-10 사이의 점수],
            "reasoning": "[평가 근거 설명 - 구체적인 UX/UI 분석과 사용자 참여도 평가]",
            "suggestions": ["[개선 제안1]", "[개선 제안2]", "[개선 제안3]"],
            "engagement_analysis": {{
                "user_experience": "[사용자 경험 분석]",
                "user_interface": "[사용자 인터페이스 분석]",
                "engagement_features": "[참여 유도 요소 분석]",
                "usability_satisfaction": "[사용성과 만족도 분석]"
            }},
            "ux_strengths": ["[UX/UI 강점1]", "[UX/UI 강점2]"],
            "usability_issues": ["[사용성 문제1]", "[사용성 문제2]"],
            "engagement_aspects": {{
                "user_experience_quality": [0-10],
                "interface_design_quality": [0-10],
                "engagement_features": [0-10],
                "usability_efficiency": [0-10],
                "user_satisfaction_potential": [0-10]
            }}
        }}
        ```

        결과는 반드시 유효한 JSON 형식이어야 합니다. 다른 텍스트는 포함하지 마세요.
        """)

    def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        실제 사용자 참여도 분석 로직을 수행합니다.
        
        Args:
            data: 전처리된 입력 데이터
            
        Returns:
            Dict: 사용자 참여도 분석 결과
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
            self.logger.error(f"사용자 참여도 분석 중 오류 발생: {str(e)}")
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
            "reasoning": result.get("reasoning", "사용자 참여도 평가가 완료되었습니다."),
            "suggestions": result.get("suggestions", []),
            "engagement_analysis": result.get("engagement_analysis", {}),
            "ux_strengths": result.get("ux_strengths", []),
            "usability_issues": result.get("usability_issues", []),
            "engagement_aspects": result.get("engagement_aspects", {})
        }
        
        # suggestions가 리스트가 아닌 경우 변환
        if not isinstance(normalized_result["suggestions"], list):
            normalized_result["suggestions"] = [str(normalized_result["suggestions"])]
        
        # 빈 suggestions인 경우 기본값 제공
        if not normalized_result["suggestions"]:
            normalized_result["suggestions"] = [
                "직관적인 사용자 인터페이스 설계로 학습 곡선 최소화",
                "개인화 기능과 맞춤형 경험 제공으로 참여도 향상",
                "게임화 요소 도입으로 사용자 동기 부여 강화"
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
            "reasoning": "사용자 참여도 평가를 완료할 수 없어 기본 점수를 제공합니다. 추가 정보가 필요합니다.",
            "suggestions": [
                "사용자 중심의 디자인 원칙 적용",
                "사용성 테스트를 통한 UX 개선",
                "참여 유도를 위한 인터랙티브 요소 추가"
            ],
            "engagement_analysis": {
                "user_experience": "정보 부족으로 분석 불가",
                "user_interface": "정보 부족으로 분석 불가",
                "engagement_features": "정보 부족으로 분석 불가",
                "usability_satisfaction": "정보 부족으로 분석 불가"
            },
            "ux_strengths": ["평가 정보 부족"],
            "usability_issues": ["사용자 참여도 분석을 위한 충분한 정보 부족"],
            "engagement_aspects": {
                "user_experience_quality": 5.0,
                "interface_design_quality": 5.0,
                "engagement_features": 5.0,
                "usability_efficiency": 5.0,
                "user_satisfaction_potential": 5.0
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