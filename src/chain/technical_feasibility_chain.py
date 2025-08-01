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


class TechnicalFeasibilityChain(EvaluationChainBase):
    """
    기술적 실현가능성 체인.
    NovaLiteLLM을 사용하여 프로젝트의 기술적 실현가능성을 평가합니다.
    """

    def __init__(self, config_path: str = "src/config/settings/evaluation/evaluation.yaml"):
        super().__init__("TechnicalFeasibilityChain")
        self._load_evaluation_criteria(config_path)
        self.llm = NovaLiteLLM()
        self.config_manager = get_config_manager()

    def _load_evaluation_criteria(self, config_path: str):
        """evaluation.yaml에서 TechnicalFeasibility 평가 기준을 로드합니다."""
        try:
            criteria = ChainUtils.load_evaluation_criteria(config_path, 'TechnicalFeasibility')
            self.pain_killer_evaluation_list = criteria['pain_killer']
            self.vitamin_evaluation_list = criteria['vitamin']
            
        except Exception as e:
            print(f"YAML 로드 실패, 기본값 사용: {e}")
            # 기본값 설정
            self.pain_killer_evaluation_list = [
                "기술이 필수적인 문제(생존/경쟁력 직결)를 해결하는가?",
                "기존 기술적 해결책의 한계가 심각한가?",
                "구현 복잡도가 비즈니스 가치에 비해 적절한가?",
                "기술적 안정성과 신뢰성이 보장되는가?"
            ]
            self.vitamin_evaluation_list = [
                "차별화된 기술적 경험을 제공하는가?",
                "사용자 편의성을 기술적으로 개선하는가?",
                "혁신적인 기술 스택을 활용하는가?",
                "확장 가능한 아키텍처를 가지고 있는가?"
            ]



    def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        EvaluationChainBase의 추상 메서드 구현.
        기술적 실현가능성 평가 로직을 실행합니다.
        
        Args:
            data: 전처리된 입력 데이터
            
        Returns:
            Dict: 분석 결과 (score, reasoning, suggestions 등 포함)
        """
        # 공통 유틸리티를 사용하여 프로젝트 타입 추출
        project_type = ChainUtils.extract_project_type(data)
        
        # 공통 유틸리티를 사용하여 입력 데이터 처리
        project_info = ChainUtils.process_input_data(data)
        
        # 기술적 실현가능성 평가 수행
        return self._evaluate_technical_feasibility(project_info, project_type)

    def _evaluate_technical_feasibility(self, project_info: str, project_type: str = "balanced") -> Dict[str, Any]:
        """
        NovaLiteLLM을 사용하여 기술적 실현가능성을 평가합니다.
        
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
        기술적 실현가능성 평가를 위한 시스템 프롬프트를 구성합니다.
        
        Args:
            project_type: 이미 분류된 프로젝트 타입
            
        Returns:
            str: 시스템 프롬프트
        """
        return ChainUtils.build_system_prompt(
            "기술적 실현가능성",
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
        return ChainUtils.build_user_prompt(project_info, "기술적 실현가능성", project_type)

    def run(self):
        """
        기술적 실현가능성 분석을 실행하고 점수를 반환합니다.
        
        Returns:
            float: 기술적 실현가능성 점수 (0-10)
        """
        # 기본 테스트용 프로젝트 정보
        test_project = "AI 기반 문서 자동 분류 시스템 개발 프로젝트"
        
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