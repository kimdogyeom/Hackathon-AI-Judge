# -*- coding: utf-8 -*-
from src.analysis.base_analysis import BaseAnalysis
from src.llm.nova_pro_llm import NovaProLLM
from src.config.config import get_system_prompt


class VideoAnalysis(BaseAnalysis):
    """
    비디오 처리기.
    비디오 데이터를 분석하여 정보를 추출합니다.
    """
    def __init__(self):
        self.llm = NovaProLLM()
        self.system_prompt = get_system_prompt('video_analysis')

    def process(self, s3_uri: str):
        """
        S3 URI에 있는 비디오를 처리하고 분석 결과를 반환합니다.

        :param s3_uri: 분석할 동영상 파일의 S3 URI
        """
        try:
            # Nova Pro 모델 호출 (시스템 프롬프트와 S3 URI 전달)
            response = self.llm.invoke(
                s3_uri=s3_uri,
                system_prompt=self.system_prompt,
                # analysis_tasks 등 추가적인 파라미터 필요 시 kwargs로 전달
            )

            # TODO: LLM 응답을 바탕으로 분석 결과를 구조화된 데이터로 반환합니다.
            processed_data = {
                "status": "completed",
                "data": response,
                "analysis_type": "video_analysis"
            }
            return processed_data
        except Exception as e:
            return {
                "status": "error",
                "reason": f"비디오 분석 중 오류 발생: {str(e)}",
                "data": {},
                "analysis_type": "video_analysis"
            }