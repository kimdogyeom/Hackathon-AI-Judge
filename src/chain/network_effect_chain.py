# -*- coding: utf-8 -*-
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import re
import yaml
from typing import Dict, Any, List
from .base_evaluation_chain import EvaluationChainBase


class NetworkEffectChain(EvaluationChainBase):
    """
    네트워크 효과 체인.
    프로젝트의 네트워크 효과와 사용자 증가에 따른 가치 증대를 평가합니다.
    
    사용자 간 상호작용, 플랫폼 효과, 바이럴 성장 가능성을 종합적으로 분석합니다.
    """

    def __init__(self, llm=None, config_path: str = "src/config/settings/evaluation/evaluation.yaml"):
        super().__init__("NetworkEffectChain")
        if llm is None:
            from src.llm.nova_lite_llm import NovaLiteLLM
            self.llm = NovaLiteLLM()
        else:
            self.llm = llm
        self.output_parser = StrOutputParser()
        self._load_evaluation_criteria(config_path)

    def _load_evaluation_criteria(self, config_path: str):
        """evaluation.yaml에서 NetworkEffect 평가 기준을 로드합니다."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                criteria = yaml.safe_load(file)
            
            network_effect = criteria.get('NetworkEffect', {})
            self.pain_killer_criteria = network_effect.get('pain_killer', [])
            self.vitamin_criteria = network_effect.get('vitamin', [])
            
        except Exception as e:
            self.logger.warning(f"평가 기준 로드 실패, 기본값 사용: {e}")
            self.pain_killer_criteria = [
                "참여자 그룹의 심각한 매칭 및 거래 문제를 해결하는가?",
                "기존 매칭/거래 방식의 한계가 심각한가?"
            ]
            self.vitamin_criteria = [
                "기존 방식의 편리함/경험을 개선하는가?",
                "차별화된 부가 가치를 제공하는가?"
            ]

        # 네트워크 효과 평가 프롬프트 템플릿
        self.prompt_template = ChatPromptTemplate.from_template("""
        ## 평가 대상: 해커톤 프로젝트 네트워크 효과 평가

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

        ## 네트워크 효과 평가 지침:
        1. **직접 네트워크 효과**: 사용자 수 증가가 기존 사용자에게 직접적 가치 제공
        2. **간접 네트워크 효과**: 한쪽 사용자 증가가 다른 사용자 그룹에게 가치 제공 (양면 시장)
        3. **데이터 네트워크 효과**: 사용자 증가로 인한 데이터 축적과 서비스 개선
        4. **소셜 네트워크 효과**: 사회적 연결과 커뮤니티 형성을 통한 가치 증대
        5. **바이럴 성장 가능성**: 사용자가 다른 사용자를 유입시키는 자연스러운 확산

        ## 네트워크 효과 평가 기준:
        {evaluation_criteria}

        ## 평가 수행:
        위 기준에 따라 {classification} 유형 프로젝트의 네트워크 효과를 0-10점 척도로 평가해주세요.
        다음 형식으로 JSON 응답을 제공해주세요:
        ```json
        {{
            "score": [0-10 사이의 점수],
            "reasoning": "[평가 근거 설명 - 구체적인 네트워크 효과 분석과 성장 가능성]",
            "suggestions": ["[개선 제안1]", "[개선 제안2]", "[개선 제안3]"],
            "network_analysis": {{
                "direct_effects": "[직접 네트워크 효과 분석]",
                "indirect_effects": "[간접 네트워크 효과 분석]",
                "data_effects": "[데이터 네트워크 효과 분석]",
                "viral_potential": "[바이럴 성장 가능성 분석]"
            }},
            "strengths": ["[네트워크 효과 강점1]", "[네트워크 효과 강점2]"],
            "limitations": ["[네트워크 효과 제약1]", "[네트워크 효과 제약2]"],
            "network_aspects": {{
                "direct_network_effect": [0-10],
                "indirect_network_effect": [0-10],
                "data_network_effect": [0-10],
                "social_network_effect": [0-10],
                "viral_growth_potential": [0-10]
            }}
        }}
        ```

        결과는 반드시 유효한 JSON 형식이어야 합니다. 다른 텍스트는 포함하지 마세요.
        """)

    def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        실제 네트워크 효과 분석 로직을 수행합니다.
        
        Args:
            data: 전처리된 입력 데이터
            
        Returns:
            Dict: 네트워크 효과 분석 결과
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
            criteria_type = "Pain Killer 기준 (필수적 네트워크 문제 해결)"
        elif project_type.lower() == 'vitamin':
            criteria = "\n".join([f"- {criteria}" for criteria in self.vitamin_criteria])
            criteria_type = "Vitamin 기준 (부가적 네트워크 가치 제공)"
        else:  # balanced
            pain_killer_criteria = "\n".join([f"- {criteria}" for criteria in self.pain_killer_criteria])
            vitamin_criteria = "\n".join([f"- {criteria}" for criteria in self.vitamin_criteria])
            criteria = f"**Pain Killer 기준:**\n{pain_killer_criteria}\n\n**Vitamin 기준:**\n{vitamin_criteria}"
            criteria_type = "Pain Killer + Vitamin 기준 (균형적 네트워크 효과)"

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
            result["evaluation_focus"] = f"{project_type} 유형 기반 네트워크 효과 평가"
            
            # 데이터 제한사항이 있는 경우 결과에 추가
            if limitations:
                result["data_limitations"] = "; ".join(limitations)
            
            return result

        except Exception as e:
            self.logger.error(f"네트워크 효과 분석 중 오류 발생: {str(e)}")
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
            "reasoning": result.get("reasoning", "네트워크 효과 평가가 완료되었습니다."),
            "suggestions": result.get("suggestions", []),
            "network_analysis": result.get("network_analysis", {}),
            "strengths": result.get("strengths", []),
            "limitations": result.get("limitations", []),
            "network_aspects": result.get("network_aspects", {})
        }
        
        # suggestions가 리스트가 아닌 경우 변환
        if not isinstance(normalized_result["suggestions"], list):
            normalized_result["suggestions"] = [str(normalized_result["suggestions"])]
        
        # 빈 suggestions인 경우 기본값 제공
        if not normalized_result["suggestions"]:
            normalized_result["suggestions"] = [
                "사용자 간 상호작용 기능 강화로 직접 네트워크 효과 증대",
                "양면 시장 구조 도입으로 간접 네트워크 효과 활용",
                "사용자 데이터 활용한 개인화 서비스로 데이터 네트워크 효과 구현"
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
            "reasoning": "네트워크 효과 평가를 완료할 수 없어 기본 점수를 제공합니다. 추가 정보가 필요합니다.",
            "suggestions": [
                "사용자 간 상호작용 요소 추가",
                "커뮤니티 기능을 통한 네트워크 효과 강화",
                "바이럴 성장을 위한 공유 및 추천 시스템 구현"
            ],
            "network_analysis": {
                "direct_effects": "정보 부족으로 분석 불가",
                "indirect_effects": "정보 부족으로 분석 불가",
                "data_effects": "정보 부족으로 분석 불가",
                "viral_potential": "정보 부족으로 분석 불가"
            },
            "strengths": ["평가 정보 부족"],
            "limitations": ["네트워크 효과 분석을 위한 충분한 정보 부족"],
            "network_aspects": {
                "direct_network_effect": 5.0,
                "indirect_network_effect": 5.0,
                "data_network_effect": 5.0,
                "social_network_effect": 5.0,
                "viral_growth_potential": 5.0
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