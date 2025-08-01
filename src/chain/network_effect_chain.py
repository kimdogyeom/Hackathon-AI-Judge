# -*- coding: utf-8 -*-
import yaml
from typing import Optional, Any, Dict

from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.utils import Input, Output

from src.llm.nova_lite_llm import NovaLiteLLM
from src.config.config_manager import get_config_manager
from src.chain.base_evaluation_chain import EvaluationChainBase
from src.chain.chain_utils import ChainUtils


class NetworkEffectChain(EvaluationChainBase):
    """
    네트워크 효과 체인.
    NovaLiteLLM을 사용하여 프로젝트의 네트워크 효과와 사용자 증가에 따른 가치 증대를 평가합니다.
    """

    def __init__(self, config_path: str = "src/config/settings/evaluation/evaluation.yaml"):
        super().__init__("NetworkEffectChain")
        self._load_evaluation_criteria(config_path)
        self.llm = NovaLiteLLM()
        self.config_manager = get_config_manager()

    def _load_evaluation_criteria(self, config_path: str):
        """evaluation.yaml에서 NetworkEffect 평가 기준을 로드합니다."""
        try:
            criteria_data = ChainUtils.load_evaluation_criteria(config_path, 'NetworkEffect')
            self.pain_killer_evaluation_list = criteria_data['pain_killer']
            self.vitamin_evaluation_list = criteria_data['vitamin']
        except Exception as e:
            print(f"YAML 로드 실패, 기본값 사용: {e}")
            # 기본값 설정
            self.pain_killer_evaluation_list = [
                "참여자 그룹의 심각한 매칭 및 거래 문제를 해결하는가?",
                "기존 매칭/거래 방식의 한계가 심각한가?",
                "네트워크 부재로 인한 심각한 비효율성을 해결하는가?"
            ]
            self.vitamin_evaluation_list = [
                "기존 방식의 편리함/경험을 개선하는가?",
                "차별화된 부가 가치를 제공하는가?",
                "사용자 간 상호작용을 통한 추가적 가치를 창출하는가?"
            ]



    def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        EvaluationChainBase의 추상 메서드 구현.
        네트워크 효과 평가 로직을 실행합니다.
        
        Args:
            data: 전처리된 입력 데이터
            
        Returns:
            Dict: 분석 결과 (score, reasoning, suggestions 등 포함)
        """
        # 공통 유틸리티를 사용하여 프로젝트 타입 추출
        project_type = ChainUtils.extract_project_type(data)
        
        # 공통 유틸리티를 사용하여 입력 데이터 처리
        project_info = ChainUtils.process_input_data(data)
        
        # 네트워크 효과 평가 수행
        return self._evaluate_network_effect(project_info, project_type)
    def _evaluate_network_effect(self, project_info: str, project_type: str = "balanced") -> Dict[str, Any]:
        """
        NovaLiteLLM을 사용하여 네트워크 효과를 평가합니다.
        
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
            
            # 공통 유틸리티를 사용하여 응답 파싱
            return ChainUtils.parse_llm_response(response, project_type)
            
        except Exception as e:
            print(f"LLM 호출 중 오류 발생: {e}")
            return ChainUtils.handle_llm_error(e, project_type)

    def _build_system_prompt(self, project_type: str = "balanced") -> str:
        """
        네트워크 효과 평가를 위한 시스템 프롬프트를 구성합니다.
        
        Args:
            project_type: 이미 분류된 프로젝트 타입
            
        Returns:
            str: 시스템 프롬프트
        """
        return ChainUtils.build_system_prompt(
            "네트워크 효과",
            self.pain_killer_evaluation_list,
            self.vitamin_evaluation_list,
            project_type
        )

    def _build_user_prompt(self, project_info: str, project_type: str = "balanced") -> str:
        """
        사용자 프롬프트를 구성합니다.
        
        Args:
            project_info: 프로젝트 정보
            project_type: 이미 분류된 프로젝트 타입
            
        Returns:
            str: 사용자 프롬프트
        """
        return ChainUtils.build_user_prompt(project_info, "네트워크 효과", project_type)

    def run(self):
        """
        네트워크 효과 분석을 실행하고 점수를 반환합니다.
        
        Returns:
            float: 네트워크 효과 점수 (0-10)
        """
        # 기본 테스트용 프로젝트 정보
        test_project = "사용자 간 상호작용을 통한 네트워크 효과 기반 플랫폼 개발 프로젝트"
        
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