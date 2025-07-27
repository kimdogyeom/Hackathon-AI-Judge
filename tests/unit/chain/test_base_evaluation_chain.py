# -*- coding: utf-8 -*-
"""
베이스 평가 체인 단위 테스트
"""
import pytest
import time
from unittest.mock import patch
from typing import Dict, Any

from src.chain.base_evaluation_chain import EvaluationChainBase


class MockEvaluationChain(EvaluationChainBase):
    """테스트용 모의 평가 체인"""
    
    def __init__(self, should_error=False):
        super().__init__("MockChain")
        self.should_error = should_error
    
    def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """모의 분석 로직"""
        if self.should_error:
            raise ValueError("테스트용 오류")
        
        # 데이터 제한사항 확인
        limitations = self._check_data_availability(data)
        
        result = {
            "score": 8.5,
            "reasoning": "모의 체인에서 생성된 평가 결과",
            "suggestions": ["개선 제안 1", "개선 제안 2"]
        }
        
        if limitations:
            result["data_limitations"] = "; ".join(limitations)
        
        return result


class TestEvaluationChainBase:
    """베이스 평가 체인 테스트 클래스"""
    
    def test_basic_invoke(self):
        """기본 invoke 메서드 테스트"""
        chain = MockEvaluationChain()
        result = chain.invoke({"content": "테스트 데이터"})
        
        # 필수 필드 확인
        assert "score" in result
        assert "reasoning" in result
        assert "suggestions" in result
        assert "execution_time" in result
        assert "chain_name" in result
        
        # 값 검증
        assert result["score"] == 8.5
        assert result["chain_name"] == "MockChain"
        assert isinstance(result["execution_time"], float)
        assert result["execution_time"] >= 0
    
    def test_input_preprocessing(self):
        """입력 데이터 전처리 테스트"""
        chain = MockEvaluationChain()
        
        # 문자열 입력
        result = chain.invoke("문자열 입력")
        assert result["score"] == 8.5
        
        # 딕셔너리 입력
        result = chain.invoke({"key": "value"})
        assert result["score"] == 8.5
        
        # 기타 타입 입력
        result = chain.invoke(123)
        assert result["score"] == 8.5
    
    def test_score_validation(self):
        """점수 유효성 검증 테스트"""
        class ScoreTestChain(EvaluationChainBase):
            def __init__(self, test_score):
                super().__init__("ScoreTest")
                self.test_score = test_score
            
            def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
                return {"score": self.test_score}
        
        # 정상 점수
        chain = ScoreTestChain(7.5)
        result = chain.invoke({})
        assert result["score"] == 7.5
        
        # 범위 초과 점수 (상한)
        chain = ScoreTestChain(15.0)
        result = chain.invoke({})
        assert result["score"] == 10.0
        
        # 범위 초과 점수 (하한)
        chain = ScoreTestChain(-5.0)
        result = chain.invoke({})
        assert result["score"] == 0.0
        
        # 잘못된 타입
        chain = ScoreTestChain("invalid")
        result = chain.invoke({})
        assert result["score"] == 0.0
    
    def test_error_handling(self):
        """오류 처리 테스트"""
        chain = MockEvaluationChain(should_error=True)
        result = chain.invoke({"content": "테스트"})
        
        # 오류 상황에서의 기본 결과 확인
        assert result["score"] == 0.0
        assert "error" in result
        assert result["status"] == "ERROR"
        assert "테스트용 오류" in result["reasoning"]
        assert result["suggestions"] == ["시스템 관리자에게 문의하세요"]
    
    def test_data_availability_check(self):
        """데이터 가용성 확인 테스트"""
        chain = MockEvaluationChain()
        
        # 모든 데이터가 있는 경우
        full_data = {
            "video_analysis": {"content": "비디오 내용"},
            "document_analysis": {"content": "문서 내용"},
            "presentation_analysis": {"content": "발표자료 내용"}
        }
        result = chain.invoke(full_data)
        assert "data_limitations" not in result
        
        # 일부 데이터가 없는 경우
        partial_data = {
            "video_analysis": {"content": "비디오 내용"},
            "document_analysis": {},
            "presentation_analysis": {"content": "발표자료 내용"}
        }
        result = chain.invoke(partial_data)
        assert "data_limitations" in result
        assert "문서 자료 부족" in result["data_limitations"]
    
    def test_execution_time_measurement(self):
        """실행 시간 측정 테스트"""
        class SlowChain(EvaluationChainBase):
            def __init__(self):
                super().__init__("SlowChain")
            
            def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
                time.sleep(0.1)  # 0.1초 대기
                return {"score": 5.0}
        
        chain = SlowChain()
        result = chain.invoke({})
        
        # 실행 시간이 0.1초 이상이어야 함
        assert result["execution_time"] >= 0.1
        assert result["execution_time"] < 0.2  # 너무 오래 걸리지 않아야 함
    
    def test_run_method_compatibility(self):
        """run 메서드 호환성 테스트"""
        chain = MockEvaluationChain()
        score = chain.run()
        
        assert isinstance(score, float)
        assert score == 8.5
    
    @patch('logging.getLogger')
    def test_logging(self, mock_logger):
        """로깅 기능 테스트"""
        chain = MockEvaluationChain()
        chain.invoke({"content": "테스트"})
        
        # 로거가 호출되었는지 확인
        mock_logger.assert_called_with("evaluation.MockChain")
    
    def test_abstract_method_enforcement(self):
        """추상 메서드 강제 구현 테스트"""
        with pytest.raises(TypeError):
            # _analyze 메서드를 구현하지 않은 클래스는 인스턴스화할 수 없어야 함
            class IncompleteChain(EvaluationChainBase):
                pass
            
            IncompleteChain()
    
    def test_standardized_output_format(self):
        """표준화된 출력 형식 테스트"""
        chain = MockEvaluationChain()
        result = chain.invoke({"content": "테스트"})
        
        # 필수 필드들이 모두 있는지 확인
        required_fields = ["score", "reasoning", "suggestions", "execution_time", "chain_name"]
        for field in required_fields:
            assert field in result, f"필수 필드 '{field}'가 결과에 없습니다"
        
        # 타입 검증
        assert isinstance(result["score"], (int, float))
        assert isinstance(result["reasoning"], str)
        assert isinstance(result["suggestions"], list)
        assert isinstance(result["execution_time"], (int, float))
        assert isinstance(result["chain_name"], str)