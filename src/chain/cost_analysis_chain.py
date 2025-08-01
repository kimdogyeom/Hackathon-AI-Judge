# -*- coding: utf-8 -*-
import yaml
import json
from typing import Optional, Any, Dict

from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.utils import Input, Output

from src.llm.nova_lite_llm import NovaLiteLLM
from src.config.config_manager import get_config_manager
from src.chain.base_evaluation_chain import EvaluationChainBase
from src.chain.chain_utils import ChainUtils


class CostAnalysisChain(EvaluationChainBase):
    """
    비용 분석 체인.
    NovaLiteLLM을 사용하여 프로젝트의 비용 효율성과 ROI를 평가합니다.
    
    evaluation.yaml의 BusinessValue 기준을 비용 관점에서 적용하여 평가합니다.
    """

    def __init__(self, config_path: str = "src/config/settings/evaluation/evaluation.yaml"):
        super().__init__("CostAnalysisChain")
        self._load_evaluation_criteria(config_path)
        self.llm = NovaLiteLLM()
        self.config_manager = get_config_manager()

    def _load_evaluation_criteria(self, config_path: str):
        """evaluation.yaml에서 BusinessValue 평가 기준을 비용 관점에서 로드합니다."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                criteria = yaml.safe_load(file)

            business_value = criteria['BusinessValue']
            self.pain_killer_evaluation_list = business_value['pain_killer']
            self.vitamin_evaluation_list = business_value['vitamin']

        except Exception as e:
            print(f"YAML 로드 실패, 기본값 사용: {e}")
            raise FileNotFoundError(e)



    def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        EvaluationChainBase의 추상 메서드 구현.
        비용 효율성 분석 로직을 실행합니다.
        
        Args:
            data: 전처리된 입력 데이터
            
        Returns:
            Dict: 분석 결과 (score, reasoning, suggestions 등 포함)
        """
        # 공통 유틸리티를 사용하여 프로젝트 타입 추출
        project_type = ChainUtils.extract_project_type(data)
        
        # 공통 유틸리티를 사용하여 입력 데이터 처리
        project_info = ChainUtils.process_input_data(data)
        
        # 비용 효율성 평가 수행
        return self._evaluate_cost_analysis(project_info, project_type)

    def _evaluate_cost_analysis(self, project_info: str, project_type: str = "balanced") -> Dict[str, Any]:
        """
        NovaLiteLLM을 사용하여 비용 효율성을 평가합니다.
        
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
            # 공통 유틸리티를 사용하여 LLM 설정 로드
            llm_config = ChainUtils.get_llm_config()
            
            # NovaLiteLLM 호출
            response = self.llm.invoke(
                user_message=user_message,
                system_message=system_message,
                temperature=llm_config['temperature'],
                max_tokens=llm_config['max_tokens']
            )
            
            # 응답 파싱 (비용 분석 특화 필드 포함)
            return self._parse_cost_analysis_response(response, project_type)
            
        except Exception as e:
            print(f"LLM 호출 중 오류 발생: {e}")
            return ChainUtils.handle_llm_error(e, project_type)

    def _build_system_prompt(self, project_type: str = "balanced") -> str:
        """
        비용 효율성 평가를 위한 시스템 프롬프트를 구성합니다.
        
        Args:
            project_type: 이미 분류된 프로젝트 타입
            
        Returns:
            str: 시스템 프롬프트
        """
        pain_killer_criteria = "\n".join([f"- {criteria}" for criteria in self.pain_killer_evaluation_list])
        vitamin_criteria = "\n".join([f"- {criteria}" for criteria in self.vitamin_evaluation_list])
        
        # 프로젝트 타입에 따른 평가 가중치 설정
        if project_type.lower() == 'painkiller':
            weight_instruction = "이 프로젝트는 PainKiller 유형으로 분류되었으므로, Pain Killer 기준에 맞춰 비용 효율성을 평가하세요."
            evaluation_criteria = pain_killer_criteria

        elif project_type.lower() == 'vitamin':
            weight_instruction = "이 프로젝트는 Vitamin 유형으로 분류되었으므로, Vitamin 기준에 맞춰 비용 효율성을 평가하세요."
            evaluation_criteria = vitamin_criteria
        else:
            weight_instruction = "이 프로젝트는 Balanced 유형으로 분류되었으므로, 두 기준을 균등하게 비용 효율성을 평가하세요."
            evaluation_criteria = pain_killer_criteria + "\n" + vitamin_criteria + "\n- 평가항목에 대해서 균등하게 적용할 수 있도록 하세요"

        return f"""당신은 비용 효율성 평가 전문가입니다. 이미 분류된 프로젝트 유형({project_type})을 고려하여 서비스의 비용 효율성과 ROI를 평가해주세요.
        
        {weight_instruction}
        
        평가 기준 (비용 관점에서 적용):
        
        **평가기준:**
        {evaluation_criteria}
        
        평가 방법:
        1. 각 기준을 비용 효율성 관점에서 1-10점으로 평가
        2. 프로젝트 타입에 따른 가중치 적용
        3. 개발 비용, 운영 비용, 예상 수익, ROI 등을 종합적으로 고려
        
        **중요: 응답은 반드시 아래 JSON 형식만으로 제공해주세요. 다른 설명이나 텍스트는 포함하지 마세요.**
        
        ```json
        {{
            "score": 숫자,
            "reasoning": "평가에 대한 상세한 근거를 설명, 점수에 대한 명확한 근거가 있어야 하며, 20년차 전문가가 봐도 납득할만한 이유여야 함.",
            "suggestions": ["개선점1", "개선점2", "개선점3"],
            "cost_breakdown": {{
                "development_cost": "개발 비용 분석",
                "operational_cost": "운영 비용 분석", 
                "expected_revenue": "예상 수익 분석",
                "roi_estimate": "ROI 추정치"
            }},
            "strengths": ["비용 효율성 강점1", "비용 효율성 강점2"],
            "risks": ["비용 리스크1", "비용 리스크2"]
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
        return f"""다음 프로젝트의 비용 효율성을 평가해주세요:

            **프로젝트 분류**: {project_type.upper()} 유형
            **프로젝트 정보**: {project_info}
            
            이미 분류된 프로젝트 유형({project_type})을 고려하여 비용 효율성을 평가하고, 반드시 JSON 형식으로만 응답해주세요."""

    def _parse_cost_analysis_response(self, response: str, project_type: str = "balanced") -> Dict[str, Any]:
        """
        비용 분석 특화 응답을 파싱합니다.
        
        Args:
            response: LLM 응답 문자열
            project_type: 프로젝트 타입
            
        Returns:
            Dict: 구조화된 비용 분석 결과
        """
        try:
            # 기본 파싱 시도
            result = ChainUtils.parse_llm_response(response, project_type)
            
            # 비용 분석 특화 필드 검증 및 기본값 설정
            if 'cost_breakdown' not in result:
                result['cost_breakdown'] = {
                    "development_cost": "정보 부족으로 분석 불가",
                    "operational_cost": "정보 부족으로 분석 불가",
                    "expected_revenue": "정보 부족으로 분석 불가",
                    "roi_estimate": "정보 부족으로 계산 불가"
                }
            
            if 'strengths' not in result:
                result['strengths'] = ["평가 정보 부족"]
            
            if 'risks' not in result:
                result['risks'] = ["비용 분석을 위한 충분한 정보 부족"]
            
            return result
            
        except Exception as e:
            print(f"비용 분석 응답 파싱 실패: {e}")
            return self._get_fallback_cost_result(project_type)

    def _get_fallback_cost_result(self, project_type: str = "balanced") -> Dict[str, Any]:
        """
        비용 분석 오류 상황에서 사용할 기본 결과를 반환합니다.
        
        Args:
            project_type: 프로젝트 타입
            
        Returns:
            Dict: 기본 비용 분석 결과
        """
        return {
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
            "project_type": project_type,
            "evaluation_method": "error_fallback"
        }
    


    def run(self):
        """
        비용 효율성 분석을 실행하고 점수를 반환합니다.
        
        Returns:
            float: 비용 효율성 점수 (0-10)
        """
        # 기본 테스트용 프로젝트 정보
        test_project = "AI 기반 비용 최적화 시스템 개발 프로젝트"
        
        result = self.invoke(test_project)
        return result.get("score", 0)

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