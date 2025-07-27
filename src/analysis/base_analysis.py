# -*- coding: utf-8 -*-
from typing import Optional, Any
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.runnables.utils import Input, Output


class BaseAnalysis(Runnable):
    """분석 클래스의 기본 클래스"""
    
    def invoke(self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Output:
        s3_uri = input.get("s3_uri")
        
        # URI가 없거나 빈 문자열인 경우 빈 결과 반환
        if not s3_uri or s3_uri.strip() == "":
            return self.get_empty_result()
        
        return self.process(s3_uri)
    
    def get_empty_result(self):
        """파일이 없을 때 반환할 기본 결과"""
        return {
            "status": "skipped",
            "reason": "파일이 제공되지 않음",
            "data": {}
        }
    
    def process(self, s3_uri: str):
        """하위 클래스에서 구현해야 하는 실제 처리 로직"""
        raise NotImplementedError("하위 클래스에서 구현해야 합니다.")