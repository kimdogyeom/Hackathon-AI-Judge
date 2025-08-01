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


class SustainabilityChain(EvaluationChainBase):
    """
    지속가능성 체인.
    NovaLiteLLM을 사용하여 프로젝트의 지속가능성을 평가합니다.
    ESG(Environmental, Social, Governance) 관점에서 장기적 지속가능성을 종합적으로 분석합니다.
    """

    def __init__(self, config_path: str = "src/config/settings/evaluation/evaluation.yaml"):
        super().__init__("SustainabilityChain")
        self._load_evaluation_criteria(config_path)
        self.llm = NovaLiteLLM()
        self.config_manager = get_config_manager()

    def _load_evaluation_criteria(self, config_path: str):
        """evaluation.yaml에서 Sustainability 평가 기준을 로드합니다."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                criteria = yaml.safe_load(file)

            sustainability = criteria['Sustainability']
            self.pain_killer_evaluation_list = sustainability['pain_killer']
            self.vitamin_evaluation_list = sustainability['vitamin']

        except Exception as e:
            print(f"YAML 로드 실패, 기본값 사용: {e}")
            raise FileNotFoundError(e)

    def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        EvaluationChainBase의 추상 메서드 구현.
        지속가능성 평가 로직을 실행합니다.
        
        Args:
            data: 전처리된 입력 데이터
            
        Returns:
            Dict: 분석 결과 (score, reasoning, suggestions 등 포함)
        """
        # 공통 유틸리티를 사용하여 프로젝트 타입 추출
        project_type = ChainUtils.extract_project_type(data)
        
        # 공통 유틸리티를 사용하여 입력 데이터 처리
        project_info = ChainUtils.process_input_data(data)
        
        # 지속가능성 평가 수행
        return self._evaluate_sustainability(project_info, project_type)

    def _evaluate_sustainability(self, project_info: str, project_type: str = "balanced") -> Dict[str, Any]:
        """
        NovaLiteLLM을 사용하여 지속가능성을 평가합니다.
        
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
        지속가능성 평가를 위한 시스템 프롬프트를 구성합니다.
        
        Args:
            project_type: 이미 분류된 프로젝트 타입
            
        Returns:
            str: 시스템 프롬프트
        """
        pain_killer_criteria = "\n".join([f"- {criteria}" for criteria in self.pain_killer_evaluation_list])
        vitamin_criteria = "\n".join([f"- {criteria}" for criteria in self.vitamin_evaluation_list])
        
        # 프로젝트 타입에 따른 평가
        if project_type.lower() == 'painkiller':
            weight_instruction = "이 프로젝트는 PainKiller 유형으로 분류되었으므로, Pain Killer 기준에 맞춰 평가하세요."
            evaluation_criteria = pain_killer_criteria
        elif project_type.lower() == 'vitamin':
            weight_instruction = "이 프로젝트는 Vitamin 유형으로 분류되었으므로, Vitamin 기준에 맞춰 평가하세요."
            evaluation_criteria = vitamin_criteria
        else:
            weight_instruction = "이 프로젝트는 Balanced 유형으로 분류되었으므로, 두 기준을 균등하게 평가하세요."
            evaluation_criteria = pain_killer_criteria + "\n" + vitamin_criteria + "\n- 평가항목에 대해서 균등하게 적용할 수 있도록 하세요"

        return f"""당신은 지속가능성 평가 전문가입니다. 이미 분류된 프로젝트 유형({project_type})을 고려하여 서비스의 지속가능성을 평가해주세요.
        
        {weight_instruction}
        
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
        
        평가 기준:
        
        **평가기준:**
        {evaluation_criteria}
        
        평가 방법:
        1. 각 기준에 대해 1-10점으로 평가
        2. 프로젝트 타입({project_type})에 따른 평가
        3. ESG 관점에서 종합적 지속가능성 분석
        
        **중요: 응답은 반드시 아래 JSON 형식만으로 제공해주세요. 다른 설명이나 텍스트는 포함하지 마세요.**
        
        ```json
        {{
            "score": 숫자,
            "reasoning": "평가에 대한 상세한 근거를 설명, 점수에 대한 명확한 근거가 있어야 하며, 20년차 전문가가 봐도 납득할만한 이유여야 함. ESG 관점에서 환경적, 사회적, 경제적, 거버넌스 측면을 종합적으로 분석.",
            "suggestions": ["개선점1", "개선점2", "개선점3"]
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
        return f"""다음 프로젝트의 지속가능성을 평가해주세요:

        **프로젝트 분류**: {project_type.upper()} 유형
        **프로젝트 정보**: {project_info}
        
        이미 분류된 프로젝트 유형({project_type})을 고려하여 ESG 관점에서 지속가능성을 평가하고, 반드시 JSON 형식으로만 응답해주세요."""

    def run(self):
        """
        지속가능성 분석을 실행하고 점수를 반환합니다.
        
        Returns:
            float: 지속가능성 점수 (0-10)
        """
        # 기본 테스트용 프로젝트 정보
        test_project = "친환경 에너지 관리 시스템 개발 프로젝트"
        
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
        return self.invoke(data)

    def as_runnable(self):
        """
        해당 클래스를 LangChain Runnable로 변환
        """
        return self