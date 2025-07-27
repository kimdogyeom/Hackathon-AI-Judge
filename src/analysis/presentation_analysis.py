# -*- coding: utf-8 -*-
from src.analysis.base_analysis import BaseAnalysis
from src.llm.nova_lite_llm import NovaLiteLLM
from src.config.config import get_system_prompt


class PresentationAnalysis(BaseAnalysis):
    """
    프레젠테이션 자료 처리기.
    PDF 형태의 프레젠테이션 자료에 대한 AI 분석을 실시합니다.
    
    지원 파일 형식: .pdf (프레젠테이션을 PDF로 변환한 파일)
    """

    def __init__(self):
        self.llm = NovaLiteLLM()
        self.system_prompt = get_system_prompt('presentation_analysis')

    def process(self, s3_uri: str):
        """
        S3 URI에 있는 프레젠테이션을 처리하고 분석 결과를 반환합니다.

        :param s3_uri: 분석할 프레젠테이션 파일의 S3 URI
        """
        try:
            # Nova Lite 모델 호출 (시스템 프롬프트와 S3 URI 전달)
            response = self.llm.invoke(
                s3_uri=s3_uri,
                system_prompt=self.system_prompt,
                # analysis_tasks 등 추가적인 파라미터 필요 시 kwargs로 전달
            )

            # TODO: LLM 응답을 바탕으로 분석 결과를 구조화된 데이터로 반환합니다.
            processed_data = {
                "status": "completed",
                "data": response,
                "analysis_type": "presentation_analysis"
            }
            return processed_data
        except Exception as e:
            return {
                "status": "error",
                "reason": f"프레젠테이션 분석 중 오류 발생: {str(e)}",
                "data": {},
                "analysis_type": "presentation_analysis"
            }