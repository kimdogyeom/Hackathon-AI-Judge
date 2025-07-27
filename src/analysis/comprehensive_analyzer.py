# -*- coding: utf-8 -*-
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


class ComprehensiveAnalyzer:
    """
    프로젝트 데이터를 종합적으로 분석하고 Pain Killer/Vitamin을 판별하는 분석기
    """

    def __init__(self, llm):
        self.llm = llm
        self.output_parser = StrOutputParser()

        # 종합 분석 프롬프트 템플릿
        self.prompt_template = ChatPromptTemplate.from_template("""
        해커톤 프로젝트 자료를 종합적으로 분석하고 Pain Killer/Vitamin을 판별해주세요.

        입력 자료: {parsed_data}

        ## 1단계: 프로젝트 종합 분석
        다음 항목들을 분석해주세요:
        - 프로젝트 개요: 
        - 핵심 기술:
        - 타겟 사용자:
        - 해결하려는 문제:
        - 주요 기능:
        - 비즈니스 모델:
        - 기술적 구현:
        - 혁신성 요소:
        - 사회적 영향:
        - 확장성:
        - 지속가능성:
        - 경쟁 우위:

        ## 2단계: Pain Killer vs Vitamin 판별
        위 분석을 바탕으로 다음 기준으로 판별해주세요:

        ### Pain Killer 판별 지표:
        1. **문제의 심각성**: 해결하지 않으면 심각한 손해/고통이 발생하는가?
        2. **현재 고통 정도**: 타겟 사용자가 현재 이 문제로 실제 고통받고 있는가?
        3. **대안의 부재**: 기존 해결책이 없거나 접근하기 어려운가?
        4. **즉각적 필요성**: 솔루션 제공 시 즉각적 완화/해결을 제공하는가?
        5. **시급성**: "지금 당장" 필요한 솔루션인가?

        ### Vitamin 판별 지표:
        1. **개선의 정도**: "더 나은", "더 편리한" 정도의 개선인가?
        2. **대안 존재**: 기존 대안이 충분히 존재하는가?
        3. **선택적 필요성**: 안 써도 일상생활에 큰 지장이 없는가?
        4. **부가적 가치**: 주로 편의성, 재미, 경험 개선에 초점인가?
        5. **점진적 필요성**: "언젠가" 있으면 좋은 솔루션인가?

        ## 3단계: 최종 판별 결과
        분석 결과:
        - **최종 분류**: [Pain Killer/Vitamin/혼재형]
        - **신뢰도**: [1-10점]
        - **주요 근거**: 
          - Pain Killer 요소: [구체적 요소들]
          - Vitamin 요소: [구체적 요소들]
        - **가중치 비율**: [Pain Killer X% + Vitamin Y%] (혼재형인 경우)
        - **핵심 특성**: [가장 강한 특성]

        ## 4단계: 평가 전략 제안
        이 분류에 따른 평가 접근 방식:
        - **중점 평가 항목**: [어떤 항목들에 집중할지]
        - **가중치 전략**: [어떤 가중치를 적용할지]
        - **기대 효과**: [이 분류가 맞다면 어떤 결과가 예상되는지]
        """)

    def __call__(self, data):
        """
        입력 데이터에 대한 종합 분석 및 Pain Killer/Vitamin 판별 수행

        :param data: 파싱된 데이터 (dict)
        :return: 종합 분석 결과 (str)
        """
        # 프롬프트 구성
        prompt = self.prompt_template.format(parsed_data=str(data))

        # LLM 호출
        response = self.llm.invoke(prompt)

        # 결과 파싱
        result = self.output_parser.invoke(response)

        return result

    def as_runnable(self):
        """
        해당 클래스를 LangChain Runnable로 변환
        """
        return lambda x: self(x["parsed_data"])
