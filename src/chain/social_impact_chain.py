# -*- coding: utf-8 -*-
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import re
import yaml
from typing import Dict, Any, List
from .base_evaluation_chain import EvaluationChainBase


class SocialImpactChain(EvaluationChainBase):
    """
    사회적 영향도 체인.
    프로젝트의 사회적 가치와 사회 문제 해결 기여도를 평가합니다.
    
    사회적 가치 창출, 포용성, 지역사회 기여, 사회 문제 해결 등을 종합적으로 분석합니다.
    """

    def __init__(self, llm=None, config_path: str = "src/config/settings/evaluation/evaluation.yaml"):
        super().__init__("SocialImpactChain")
        if llm is None:
            from src.llm.nova_lite_llm import NovaLiteLLM
            self.llm = NovaLiteLLM()
        else:
            self.llm = llm
        self.output_parser = StrOutputParser()
        self._load_evaluation_criteria(config_path)

    def _load_evaluation_criteria(self, config_path: str):
        """evaluation.yaml에서 SocialImpact 평가 기준을 로드합니다."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                criteria = yaml.safe_load(file)
            
            social_impact = criteria.get('SocialImpact', {})
            self.pain_killer_criteria = social_impact.get('pain_killer', [])
            self.vitamin_criteria = social_impact.get('vitamin', [])
            
        except Exception as e:
            self.logger.warning(f"평가 기준 로드 실패, 기본값 사용: {e}")
            self.pain_killer_criteria = [
                "자료에서 제시한 사회적 약자의 문제가 생존 및 안전과 직결하는가?",
                "기존 지원 시스템의 한계가 심각한가?"
            ]
            self.vitamin_criteria = [
                "장기적인 사회적 가치를 제공하는가?",
                "사회적 인식 개선에 기여하는가?"
            ]

        # 사회적 영향도 평가 프롬프트 템플릿
        self.prompt_template = ChatPromptTemplate.from_template("""
        ## 평가 대상: 해커톤 프로젝트 사회적 영향도 평가

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

        ## 사회적 영향도 평가 지침:
        1. **사회 문제 해결**: 실제 사회 문제를 해결하거나 완화하는 정도
        2. **사회적 가치 창출**: 경제적 이익을 넘어선 사회적 가치 제공
        3. **포용성과 접근성**: 소외계층이나 취약계층의 접근성 고려
        4. **지역사회 기여**: 지역사회 발전과 상생에 기여하는 정도
        5. **지속가능한 사회적 변화**: 장기적이고 지속가능한 사회적 변화 유도

        ## 사회적 영향도 평가 기준:
        {evaluation_criteria}

        ## 평가 수행:
        위 기준에 따라 {classification} 유형 프로젝트의 사회적 영향도를 0-10점 척도로 평가해주세요.
        다음 형식으로 JSON 응답을 제공해주세요:
        ```json
        {{
            "score": [0-10 사이의 점수],
            "reasoning": "[평가 근거 설명 - 구체적인 사회적 영향과 기여도 분석]",
            "suggestions": ["[개선 제안1]", "[개선 제안2]", "[개선 제안3]"],
            "impact_analysis": {{
                "problem_solving": "[사회 문제 해결 분석]",
                "value_creation": "[사회적 가치 창출 분석]",
                "inclusivity": "[포용성 및 접근성 분석]",
                "community_contribution": "[지역사회 기여 분석]"
            }},
            "target_beneficiaries": ["[수혜 대상1]", "[수혜 대상2]"],
            "social_challenges": ["[해결하는 사회 문제1]", "[해결하는 사회 문제2]"],
            "impact_aspects": {{
                "problem_solving_effectiveness": [0-10],
                "social_value_creation": [0-10],
                "inclusivity_accessibility": [0-10],
                "community_contribution": [0-10],
                "sustainability": [0-10]
            }}
        }}
        ```

        결과는 반드시 유효한 JSON 형식이어야 합니다. 다른 텍스트는 포함하지 마세요.
        """)

    def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        실제 사회적 영향도 분석 로직을 수행합니다.
        
        Args:
            data: 전처리된 입력 데이터
            
        Returns:
            Dict: 사회적 영향도 분석 결과
        """
        # 데이터 제한사항 확인
        limitations = self._check_data_availability(data)
        
        # 이미 분류된 프로젝트 타입 추출
        project_type = "balanced"  # 기본값
        if 'project_type' in data:
            project_type = data['project_type']
        elif 'classification' in data and isinstance(data['classification'], dict):
            project_type = data['classification'].get('project_type', 'balanced')
        
        # 필요한 데이터 추출
        parsed_data = data.get("parsed_data", {})
        classification = project_type  # 이미 분류된 타입 사용
        material_analysis = data.get("material_analysis", "")
        
        # 데이터 제한사항 메시지 생성
        limitations_text = ""
        if limitations:
            limitations_text = "다음 제한사항이 있습니다: " + ", ".join(limitations)
        else:
            limitations_text = "모든 자료가 충분히 제공되었습니다."

        # 프로젝트 타입에 따른 평가 기준 선택
        if project_type.lower() == 'painkiller':
            criteria = "\n".join([f"- {criteria}" for criteria in self.pain_killer_criteria])
            criteria_type = "Pain Killer 기준 (필수적 사회적 문제 해결)"
        elif project_type.lower() == 'vitamin':
            criteria = "\n".join([f"- {criteria}" for criteria in self.vitamin_criteria])
            criteria_type = "Vitamin 기준 (부가적 사회적 가치 제공)"
        else:  # balanced
            pain_killer_criteria = "\n".join([f"- {criteria}" for criteria in self.pain_killer_criteria])
            vitamin_criteria = "\n".join([f"- {criteria}" for criteria in self.vitamin_criteria])
            criteria = f"**Pain Killer 기준:**\n{pain_killer_criteria}\n\n**Vitamin 기준:**\n{vitamin_criteria}"
            criteria_type = "Pain Killer + Vitamin 기준 (균형적 사회적 영향)"

        # 프롬프트 구성
        prompt = self.prompt_template.format(
            project_name=parsed_data.get("project_name", "정보 없음"),
            description=parsed_data.get("description", "정보 없음"),
            technology=parsed_data.get("technology", "정보 없음"),
            target_users=parsed_data.get("target_users", "정보 없음"),
            business_model=parsed_data.get("business_model", "정보 없음"),
            classification=f"{classification.upper()} ({criteria_type})",
            material_analysis=material_analysis or "종합 분석 정보가 제공되지 않았습니다.",
            data_limitations=limitations_text,
            evaluation_criteria=f"**{criteria_type}:**\n{criteria}"
        )

        try:
            # LLM 호출
            response = self.llm.invoke(prompt)
            result_text = self.output_parser.invoke(response)

            # JSON 파싱
            result = self._parse_llm_response(result_text)
            
            # 프로젝트 타입 정보 추가
            result["project_type"] = project_type
            result["evaluation_focus"] = f"{project_type} 유형 기반 사회적 영향도 평가"
            
            # 데이터 제한사항이 있는 경우 결과에 추가
            if limitations:
                result["data_limitations"] = "; ".join(limitations)
            
            return result

        except Exception as e:
            self.logger.error(f"사회적 영향도 분석 중 오류 발생: {str(e)}")
            return self._get_fallback_result(limitations, project_type)
    
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
            "reasoning": result.get("reasoning", "사회적 영향도 평가가 완료되었습니다."),
            "suggestions": result.get("suggestions", []),
            "impact_analysis": result.get("impact_analysis", {}),
            "target_beneficiaries": result.get("target_beneficiaries", []),
            "social_challenges": result.get("social_challenges", []),
            "impact_aspects": result.get("impact_aspects", {})
        }
        
        # suggestions가 리스트가 아닌 경우 변환
        if not isinstance(normalized_result["suggestions"], list):
            normalized_result["suggestions"] = [str(normalized_result["suggestions"])]
        
        # 빈 suggestions인 경우 기본값 제공
        if not normalized_result["suggestions"]:
            normalized_result["suggestions"] = [
                "구체적인 사회 문제 해결 방안 명시",
                "소외계층을 위한 접근성 개선 방안 추가",
                "지역사회와의 협력 체계 구축"
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
    
    def _get_fallback_result(self, limitations: List[str] = None, project_type: str = "balanced") -> Dict[str, Any]:
        """
        오류 상황에서 사용할 기본 결과를 반환합니다.
        
        Args:
            limitations: 데이터 제한사항 목록
            
        Returns:
            Dict: 기본 결과
        """
        result = {
            "score": 5.0,
            "reasoning": "사회적 영향도 평가를 완료할 수 없어 기본 점수를 제공합니다. 추가 정보가 필요합니다.",
            "suggestions": [
                "해결하고자 하는 사회 문제 명확히 정의",
                "사회적 가치 창출 방안 구체화",
                "수혜 대상과 영향 범위 명시"
            ],
            "impact_analysis": {
                "problem_solving": "정보 부족으로 분석 불가",
                "value_creation": "정보 부족으로 분석 불가",
                "inclusivity": "정보 부족으로 분석 불가",
                "community_contribution": "정보 부족으로 분석 불가"
            },
            "target_beneficiaries": ["평가 정보 부족"],
            "social_challenges": ["사회적 영향 분석을 위한 충분한 정보 부족"],
            "impact_aspects": {
                "problem_solving_effectiveness": 5.0,
                "social_value_creation": 5.0,
                "inclusivity_accessibility": 5.0,
                "community_contribution": 5.0,
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