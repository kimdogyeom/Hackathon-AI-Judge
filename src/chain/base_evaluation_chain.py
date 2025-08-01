# -*- coding: utf-8 -*-
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.runnables.utils import Input, Output


class EvaluationChainBase(Runnable, ABC):
    """
    모든 평가 체인이 상속받을 공통 베이스 클래스.
    
    표준화된 입력/출력 형식, 실행 시간 측정, 로깅, 오류 처리 기능을 제공합니다.
    """
    
    def __init__(self, chain_name: str = None):
        """
        베이스 클래스 초기화.
        
        Args:
            chain_name: 체인 이름 (로깅용)
        """
        super().__init__()
        self.chain_name = chain_name or self.__class__.__name__
        self.logger = logging.getLogger(f"evaluation.{self.chain_name}")
        
        # 로깅 설정
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def invoke(self, input: Input, config: Optional[RunnableConfig] = None, **kwargs: Any) -> Output:
        """
        표준화된 평가 실행 메서드 - 기존 체인과 호환.
        
        Args:
            input: 평가할 입력 데이터
            config: 실행 설정 (선택)
            **kwargs: 추가 파라미터
            
        Returns:
            Dict: 표준화된 평가 결과
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"{self.chain_name} 평가 시작")
            
            # 입력 데이터 검증 및 전처리
            processed_input = self._preprocess_input(input)
            
            # 실제 분석 로직 실행
            analysis_result = self._analyze(processed_input)
            
            # 결과 후처리 및 표준화
            standardized_result = self._postprocess_result(analysis_result, start_time)
            
            self._log_execution(start_time, "SUCCESS")
            self.logger.info(f"{self.chain_name} 평가 완료 - 점수: {standardized_result.get('score', 'N/A')}")
            
            return standardized_result
            
        except Exception as e:
            self._log_execution(start_time, "ERROR")
            self.logger.error(f"{self.chain_name} 평가 중 오류 발생: {str(e)}")
            return self._handle_error(e, start_time)
    
    def _preprocess_input(self, input_data: Input) -> Dict[str, Any]:
        """
        입력 데이터를 전처리하여 표준화된 형식으로 변환.
        
        Args:
            input_data: 원본 입력 데이터
            
        Returns:
            Dict: 전처리된 입력 데이터
        """
        if isinstance(input_data, str):
            return {"content": input_data}
        elif isinstance(input_data, dict):
            return input_data
        else:
            return {"content": str(input_data)}
    
    def _postprocess_result(self, analysis_result: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """
        분석 결과를 표준화된 형식으로 후처리.
        
        Args:
            analysis_result: 원본 분석 결과
            start_time: 실행 시작 시간
            
        Returns:
            Dict: 표준화된 결과
        """
        execution_time = time.time() - start_time
        
        # 기본 구조 생성
        standardized_result = {
            "score": self._extract_score(analysis_result),
            "reasoning": analysis_result.get("reasoning", ""),
            "suggestions": analysis_result.get("suggestions", []),
            "execution_time": round(execution_time, 3),
            "chain_name": self.chain_name
        }
        
        # 데이터 제한사항이 있는 경우 추가
        if "data_limitations" in analysis_result:
            standardized_result["data_limitations"] = analysis_result["data_limitations"]
        
        # 추가 메타데이터가 있는 경우 포함
        for key, value in analysis_result.items():
            if key not in ["score", "reasoning", "suggestions", "data_limitations"]:
                standardized_result[key] = value
        
        return standardized_result
    
    def _extract_score(self, analysis_result: Dict[str, Any]) -> float:
        """
        분석 결과에서 점수를 추출하고 유효성을 검증.
        
        Args:
            analysis_result: 분석 결과
            
        Returns:
            float: 0.0-10.0 범위의 점수
        """
        score = analysis_result.get("score", 0.0)
        
        # 점수 타입 변환 및 유효성 검증
        try:
            score = float(score)
            return max(0.0, min(10.0, score))
        except (ValueError, TypeError):
            self.logger.warning(f"유효하지 않은 점수 값: {score}, 기본값 0.0 사용")
            return 0.0
    
    def _handle_error(self, error: Exception, start_time: float) -> Dict[str, Any]:
        """
        일관된 오류 처리 및 기본 결과 반환.
        
        Args:
            error: 발생한 오류
            start_time: 실행 시작 시간
            
        Returns:
            Dict: 오류 상황에서의 기본 결과
        """
        execution_time = time.time() - start_time
        
        return {
            "score": 0.0,
            "reasoning": f"평가 중 오류가 발생했습니다: {str(error)}",
            "suggestions": ["시스템 관리자에게 문의하세요"],
            "execution_time": round(execution_time, 3),
            "chain_name": self.chain_name,
            "error": str(error),
            "status": "ERROR"
        }
    
    def _log_execution(self, start_time: float, status: str):
        """
        실행 로깅.
        
        Args:
            start_time: 실행 시작 시간
            status: 실행 상태 (SUCCESS, ERROR 등)
        """
        execution_time = time.time() - start_time
        self.logger.info(
            f"{self.chain_name} 실행 완료 - 상태: {status}, 실행시간: {execution_time:.3f}초"
        )
    
    def _check_data_availability(self, input_data: Dict[str, Any]) -> List[str]:
        """
        입력 데이터의 가용성을 확인하고 제한사항을 반환.
        
        Args:
            input_data: 입력 데이터
            
        Returns:
            List[str]: 데이터 제한사항 목록
        """
        limitations = []
        
        # 비디오 데이터 확인
        video_data = input_data.get("video_analysis", {})
        if not video_data or not video_data.get("content"):
            limitations.append("비디오 자료 부족으로 인한 평가 제한")
        
        # 문서 데이터 확인
        document_data = input_data.get("document_analysis", {})
        if not document_data or not document_data.get("content"):
            limitations.append("문서 자료 부족으로 인한 평가 제한")
        
        # 발표자료 데이터 확인
        presentation_data = input_data.get("presentation_analysis", {})
        if not presentation_data or not presentation_data.get("content"):
            limitations.append("발표자료 부족으로 인한 평가 제한")
        
        return limitations
    
    @abstractmethod
    def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        실제 분석 로직 (하위 클래스에서 구현).
        
        Args:
            data: 전처리된 입력 데이터
            
        Returns:
            Dict: 분석 결과 (score, reasoning, suggestions 등 포함)
        """
        pass
    
    def run(self) -> float:
        """
        기존 호환성을 위한 run 메서드.
        
        Returns:
            float: 평가 점수
        """
        result = self.invoke({})
        return result.get("score", 0.0)

