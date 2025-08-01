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


class UserEngagementChain(EvaluationChainBase):
    """
    사용자 참여도 체인.
    NovaLiteLLM을 사용하여 프로젝트의 사용자 참여도를 평가합니다.
    """

    def __init__(self, config_path: str = "src/config/settings/evaluation/evaluation.yaml"):
        super().__init__("UserEngagementChain")
        self._load_evaluation_criteria(config_path)
        self.llm = NovaLiteLLM()
        self.config_manager = get_config_manager()

    def _load_evaluation_criteria(self, config_path: str):
        """evaluation.yaml에서 UserEngagement 평가 기준을 로드합니다."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                criteria = yaml.safe_load(file)

            user_engagement = criteria['UserEngagement']
            self.pain_killer_evaluation_list = user_engagement['pain_killer']
            self.vitamin_evaluation_list = user_engagement['vitamin']

        except Exception as e:
            print(f"YAML 로드 실패, 기본값 사용: {e}")
            raise FileNotFoundError(e)



    def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        EvaluationChainBase의 추상 메서드 구현.
        사용자 참여도 평가 로직을 실행합니다.
        
        Args:
            data: 전처리된 입력 데이터
            
        Returns:
            Dict: 분석 결과 (score, reasoning, suggestions 등 포함)
        """
        # 공통 유틸리티를 사용하여 프로젝트 타입 추출
        project_type = ChainUtils.extract_project_type(data)
        
        # 공통 유틸리티를 사용하여 입력 데이터 처리
        project_info = ChainUtils.process_input_data(data)
        
        # 사용자 참여도 평가 수행
        return self._evaluate_user_engagement(project_info, project_type)


    def _evaluate_user_engagement(self, project_info: str, project_type: str = "balanced") -> Dict[str, Any]:
        """
        NovaLiteLLM을 사용하여 사용자 참여도를 평가합니다.
        
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
            result = ChainUtils.parse_llm_response(response, project_type)
            
            # 사용자 참여도 평가에 특화된 결과 검증 및 보완
            return self._validate_user_engagement_result(result, project_type)
            
        except Exception as e:
            print(f"LLM 호출 중 오류 발생: {e}")
            return self._get_user_engagement_fallback_result(e, project_type)

    def _build_system_prompt(self, project_type: str = "balanced") -> str:
        """
        사용자 참여도 평가를 위한 시스템 프롬프트를 구성합니다.
        
        Args:
            project_type: 이미 분류된 프로젝트 타입
            
        Returns:
            str: 시스템 프롬프트
        """
        pain_killer_criteria = "\n".join([f"- {criteria}" for criteria in self.pain_killer_evaluation_list])
        vitamin_criteria = "\n".join([f"- {criteria}" for criteria in self.vitamin_evaluation_list])
        
        # 프로젝트 타입에 따른 평가 가중치 설정
        if project_type.lower() == 'painkiller':
            weight_instruction = "이 프로젝트는 PainKiller 유형으로 분류되었으므로, Pain Killer 기준에 맞춰 평가하세요."
            evaluation_criteria = pain_killer_criteria

        elif project_type.lower() == 'vitamin':
            weight_instruction = "이 프로젝트는 Vitamin 유형으로 분류되었으므로, Vitamin 기준에 맞춰 평가하세요."
            evaluation_criteria = vitamin_criteria
        else:
            weight_instruction = "이 프로젝트는 Balanced 유형으로 분류되었으므로, 두 기준을 균등하게 평가하세요."
            evaluation_criteria = pain_killer_criteria + vitamin_criteria + "평가항목에 대해서 균등하게 적용할 수 있도록 하세요"

        return f"""당신은 사용자 참여도 평가 전문가입니다. 이미 분류된 프로젝트 유형({project_type})을 고려하여 서비스의 사용자 참여도를 평가해주세요.
        
        {weight_instruction}
        
        ## 사용자 참여도 평가 영역:
        1. **사용자 경험 (UX)**: 사용자 여정, 직관성, 학습 곡선, 니즈 충족도
        2. **사용자 인터페이스 (UI)**: 시각적 디자인, 일관성, 반응형 디자인, 접근성
        3. **참여 유도 요소**: 게임화, 개인화, 소셜 기능, 커뮤니티 요소
        4. **사용성과 만족도**: 편의성, 효율성, 오류 처리, 전반적 만족도
        
        ## 프로젝트 타입별 평가 기준:
        **{project_type.upper()} 유형 기준:**
        {evaluation_criteria}
        
        평가 방법:
        1. 각 기준에 대해 1-10점으로 평가
        2. 프로젝트 타입({project_type})에 따른 가중치 적용
        3. 사용자 참여도의 4가지 영역을 종합적으로 고려
        
        **중요: 응답은 반드시 아래 JSON 형식만으로 제공해주세요. 다른 설명이나 텍스트는 포함하지 마세요.**
        
        ```json
        {{
            "score": 숫자,
            "reasoning": "평가에 대한 상세한 근거를 설명, 점수에 대한 명확한 근거가 있어야 하며, 20년차 전문가가 봐도 납득할만한 이유여야 함. UX/UI, 참여 유도 요소, 사용성 관점에서 구체적으로 분석.",
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
        return f"""다음 프로젝트의 사용자 참여도를 평가해주세요:

**프로젝트 분류**: {project_type.upper()} 유형
**프로젝트 정보**: {project_info}

**평가 요청사항**:
- 사용자 경험(UX) 품질 분석
- 사용자 인터페이스(UI) 디자인 평가  
- 참여 유도 요소 및 게임화 분석
- 사용성과 전반적 만족도 평가
- {project_type} 유형에 특화된 사용자 참여도 기준 적용

이미 분류된 프로젝트 유형({project_type})을 고려하여 평가하고, 반드시 JSON 형식으로만 응답해주세요."""

    def _validate_user_engagement_result(self, result: Dict[str, Any], project_type: str) -> Dict[str, Any]:
        """
        사용자 참여도 평가 결과를 검증하고 보완합니다.
        
        Args:
            result: ChainUtils로 파싱된 기본 결과
            project_type: 프로젝트 타입
            
        Returns:
            Dict: 검증 및 보완된 결과
        """
        # 기본 필드 검증
        validated_result = {
            "score": ChainUtils.validate_score(result.get("score", 0)),
            "reasoning": result.get("reasoning", ""),
            "suggestions": result.get("suggestions", []),
            "project_type": project_type,
            "evaluation_method": result.get("evaluation_method", "llm_based_with_classification")
        }
        
        # reasoning이 비어있거나 너무 짧은 경우 기본값 제공
        if not validated_result["reasoning"] or len(validated_result["reasoning"]) < 20:
            validated_result["reasoning"] = f"사용자 참여도를 {validated_result['score']}점으로 평가했습니다. {project_type} 유형 프로젝트의 특성을 고려한 평가입니다."
        
        # suggestions가 비어있거나 부족한 경우 기본값 제공
        if not validated_result["suggestions"] or len(validated_result["suggestions"]) < 2:
            default_suggestions = self._get_default_suggestions(project_type)
            validated_result["suggestions"] = default_suggestions
        
        # suggestions가 3개를 초과하는 경우 상위 3개만 선택
        if len(validated_result["suggestions"]) > 3:
            validated_result["suggestions"] = validated_result["suggestions"][:3]
        
        # 사용자 참여도 평가 특화 정보 추가
        validated_result["evaluation_focus"] = self._get_evaluation_focus(project_type)
        
        return validated_result

    def _get_default_suggestions(self, project_type: str) -> list:
        """
        프로젝트 타입별 기본 개선 제안사항을 반환합니다.
        
        Args:
            project_type: 프로젝트 타입
            
        Returns:
            list: 기본 개선 제안사항 목록
        """
        if project_type.lower() == 'painkiller':
            return [
                "사용자의 감정적 고통 해결을 위한 직관적이고 간단한 인터페이스 설계",
                "접근성 문제 해결을 위한 다양한 플랫폼 지원 및 오프라인 기능 제공",
                "치료적/교육적 기능의 사용성 개선을 통한 효과적인 문제 해결"
            ]
        elif project_type.lower() == 'vitamin':
            return [
                "게임화 요소와 재미 요소를 통한 사용자 참여도 향상",
                "커뮤니티 기능과 소셜 요소를 통한 소속감 및 몰입도 증대",
                "개인화된 경험과 맞춤형 콘텐츠를 통한 사용자 만족도 개선"
            ]
        else:  # balanced
            return [
                "실용적 문제 해결과 즐거운 경험의 균형잡힌 사용자 인터페이스 설계",
                "접근성과 편의성을 동시에 고려한 포용적 디자인 적용",
                "사용자 니즈 충족과 참여 유도 요소의 조화로운 통합"
            ]

    def _get_evaluation_focus(self, project_type: str) -> str:
        """
        프로젝트 타입별 평가 초점을 반환합니다.
        
        Args:
            project_type: 프로젝트 타입
            
        Returns:
            str: 평가 초점 설명
        """
        if project_type.lower() == 'painkiller':
            return "감정적 고통 해결과 접근성 개선에 중점을 둔 사용자 참여도 평가"
        elif project_type.lower() == 'vitamin':
            return "오락성과 사용자 만족도 향상에 중점을 둔 사용자 참여도 평가"
        else:  # balanced
            return "실용성과 즐거움의 균형을 고려한 종합적 사용자 참여도 평가"

    def _get_user_engagement_fallback_result(self, error: Exception, project_type: str) -> Dict[str, Any]:
        """
        사용자 참여도 평가 실패 시 특화된 fallback 결과를 반환합니다.
        
        Args:
            error: 발생한 오류
            project_type: 프로젝트 타입
            
        Returns:
            Dict: 사용자 참여도 평가 특화 fallback 결과
        """
        # 기본 오류 처리 결과 가져오기
        base_result = ChainUtils.handle_llm_error(error, project_type)
        
        # 사용자 참여도 평가 특화 정보 추가
        base_result.update({
            "reasoning": f"사용자 참여도 평가 중 오류가 발생했습니다: {str(error)}. 기본 평가 점수를 제공합니다.",
            "suggestions": self._get_default_suggestions(project_type),
            "evaluation_focus": self._get_evaluation_focus(project_type),
            "evaluation_method": "user_engagement_fallback"
        })
        
        return base_result

    def run(self):
        """
        사용자 참여도 분석을 실행하고 점수를 반환합니다.
        
        Returns:
            float: 사용자 참여도 점수 (0-10)
        """
        # 기본 테스트용 프로젝트 정보
        test_project = "AI 기반 사용자 맞춤형 학습 플랫폼 개발 프로젝트"
        
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