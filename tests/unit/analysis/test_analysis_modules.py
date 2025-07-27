# -*- coding: utf-8 -*-
"""
분석 모듈 통합 테스트
"""

import pytest
import logging
from src.analysis.document_analysis import DocumentAnalysis
from src.analysis.presentation_analysis import PresentationAnalysis
from src.analysis.video_analysis import VideoAnalysis

# 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 핸들러가 없으면 추가
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class TestAnalysisModules:
    """분석 모듈들의 통합 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.document_analysis = DocumentAnalysis()
        self.presentation_analysis = PresentationAnalysis()
        self.video_analysis = VideoAnalysis()
    
    # document_analysis 테스트
    def test_document_analysis_empty_uri(self):
        """DocumentAnalysis 빈 URI 처리 테스트"""
        result = self.document_analysis.invoke({"s3_uri": ""})
        
        assert result["status"] == "skipped"
        assert "reason" in result
    
    def test_document_analysis_none_uri(self):
        """DocumentAnalysis None URI 처리 테스트"""
        result = self.document_analysis.invoke({"s3_uri": None})
        
        assert result["status"] == "skipped"
        assert "reason" in result
    
    def test_document_analysis_missing_uri(self):
        """DocumentAnalysis URI 누락 처리 테스트"""
        result = self.document_analysis.invoke({})
        
        assert result["status"] == "skipped"
        assert "reason" in result
        
    def test_document_analysis_valid_uri(self):
        """DocumentAnalysis 유효한 URI 처리 테스트"""
        valid_uri = "https://s3.us-east-1.amazonaws.com/victor.kim-temporary/hackathon/ongi_project_description.txt"
        result = self.document_analysis.invoke({"s3_uri": valid_uri})

        logger.info(f"test_document_analysis_valid_uri 출력 데이터 확인: {result.get('data', 'No data')}")
        
        # 성공하거나 적절한 오류 처리가 되어야 함
        assert "status" in result
        if result["status"] == "completed":
            assert "data" in result or "analysis_result" in result or "content" in result
        elif result["status"] == "error":
            assert "error" in result
    
    
    # presentation_analysis 테스트
    def test_presentation_analysis_empty_uri(self):
        """PresentationAnalysis 빈 URI 처리 테스트"""
        result = self.presentation_analysis.invoke({"s3_uri": ""})
        
        assert result["status"] == "skipped"
        assert "reason" in result
    
    def test_presentation_analysis_none_uri(self):
        """PresentationAnalysis None URI 처리 테스트"""
        result = self.presentation_analysis.invoke({"s3_uri": None})
        
        assert result["status"] == "skipped"
        assert "reason" in result
    
    def test_presentation_analysis_missing_uri(self):
        """PresentationAnalysis URI 누락 처리 테스트"""
        result = self.presentation_analysis.invoke({})
        
        assert result["status"] == "skipped"
        assert "reason" in result
        
    def test_presentation_analysis_valid_uri(self):
        """PresentationAnalysis 유효한 URI 처리 테스트"""
        valid_uri = "https://s3.us-east-1.amazonaws.com/victor.kim-temporary/hackathon/carenity.pdf"
        result = self.presentation_analysis.invoke({"s3_uri": valid_uri})
        
        logger.info(f"test_presentation_analysis_valid_uri 출력 데이터 확인: {result.get('data', 'No data')}")
        
        
        # 성공하거나 적절한 오류 처리가 되어야 함
        assert "status" in result
        if result["status"] == "completed":
            assert "data" in result or "analysis_result" in result or "content" in result
        elif result["status"] == "error":
            assert "error" in result
    
    
    # video_analysis 테스트
    def test_video_analysis_empty_uri(self):
        """VideoAnalysis 빈 URI 처리 테스트"""
        result = self.video_analysis.invoke({"s3_uri": ""})
        
        assert result["status"] == "skipped"
        assert "reason" in result
    
    def test_video_analysis_none_uri(self):
        """VideoAnalysis None URI 처리 테스트"""
        result = self.video_analysis.invoke({"s3_uri": None})
        
        assert result["status"] == "skipped"
        assert "reason" in result
    
    def test_video_analysis_missing_uri(self):
        """VideoAnalysis URI 누락 처리 테스트"""
        result = self.video_analysis.invoke({})
        
        assert result["status"] == "skipped"
        assert "reason" in result
        
    def test_video_analysis_valid_uri(self):
        """VideoAnalysis 유효한 URI 처리 테스트"""
        valid_uri = "https://s3.us-east-1.amazonaws.com/victor.kim-temporary/hackathon/%EC%B2%B4%EB%A6%AC%EC%98%A8%ED%83%91+GenAi+%ED%95%B4%EC%BB%A4%ED%86%A4+%EB%B0%9C%ED%91%9C%EC%98%81%EC%83%81.mp4"
        result = self.video_analysis.invoke({"s3_uri": valid_uri})
        
        logger.info(f"test_video_analysis_valid_uri 출력 데이터 확인: {result.get('data', 'No data')}")
        
        # 성공하거나 적절한 오류 처리가 되어야 함
        assert "status" in result
        if result["status"] == "completed":
            assert "data" in result or "analysis_result" in result or "content" in result
        elif result["status"] == "error":
            assert "reason" in result
    
    
    
    
    def test_all_modules_interface_consistency(self):
        """모든 분석 모듈의 인터페이스 일관성 테스트"""
        modules = [
            self.document_analysis,
            self.presentation_analysis,
            self.video_analysis
        ]
        
        test_input = {"s3_uri": ""}
        
        for module in modules:
            result = module.invoke(test_input)
            
            # 모든 모듈이 동일한 기본 구조를 반환해야 함
            assert isinstance(result, dict)
            assert "status" in result
            
            # 스킵된 경우 reason이 있어야 함
            if result["status"] == "skipped":
                assert "reason" in result
    
    def test_modules_with_different_input_formats(self):
        """다양한 입력 형식에 대한 모듈 테스트"""
        test_inputs = [
            {},  # 빈 딕셔너리
            {"s3_uri": ""},  # 빈 URI
            {"s3_uri": None},  # None URI
            {"other_key": "value"},  # s3_uri 키 없음
        ]
        
        modules = [
            ("DocumentAnalysis", self.document_analysis),
            ("PresentationAnalysis", self.presentation_analysis),
            ("VideoAnalysis", self.video_analysis)
        ]
        
        for module_name, module in modules:
            for i, test_input in enumerate(test_inputs):
                result = module.invoke(test_input)
                
                # 모든 경우에 적절한 응답이 있어야 함
                assert isinstance(result, dict), f"{module_name} failed on input {i}"
                assert "status" in result, f"{module_name} missing status on input {i}"
                
                # 잘못된 입력에 대해서는 스킵되어야 함
                assert result["status"] == "skipped", f"{module_name} should skip on input {i}"
    
    def test_modules_error_handling(self):
        """모듈들의 오류 처리 테스트"""
        # 잘못된 형식의 입력
        invalid_inputs = [
            "string_input",  # 문자열 (딕셔너리가 아님)
            123,  # 숫자
            None,  # None
            [],  # 리스트
        ]
        
        modules = [
            self.document_analysis,
            self.presentation_analysis,
            self.video_analysis
        ]
        
        for module in modules:
            for invalid_input in invalid_inputs:
                try:
                    result = module.invoke(invalid_input)
                    # 오류가 발생하지 않았다면 적절한 오류 상태를 반환해야 함
                    assert isinstance(result, dict)
                    assert result.get("status") in ["skipped", "error"]
                except Exception:
                    # 예외가 발생하는 것도 허용 (모듈에 따라 다를 수 있음)
                    pass
    
    def test_runnable_interface_compliance(self):
        """Runnable 인터페이스 준수 테스트"""
        modules = [
            self.document_analysis,
            self.presentation_analysis,
            self.video_analysis
        ]
        
        for module in modules:
            # invoke 메서드가 있어야 함
            assert hasattr(module, 'invoke')
            assert callable(module.invoke)
            
            # 기본 입력으로 호출 가능해야 함
            result = module.invoke({"s3_uri": ""})
            assert isinstance(result, dict)


class TestAnalysisIntegration:
    """분석 모듈들의 통합 시나리오 테스트"""
    
    def test_mixed_analysis_scenario(self):
        """혼합 분석 시나리오 테스트 (일부는 성공, 일부는 스킵)"""
        document_analysis = DocumentAnalysis()
        presentation_analysis = PresentationAnalysis()
        video_analysis = VideoAnalysis()
        
        # 실제 시나리오와 유사한 입력
        inputs = {
            "video_analysis": {"s3_uri": ""},  # 빈 URI (스킵 예상)
            "document_analysis": {"s3_uri": ""},  # 빈 URI (스킵 예상)
            "presentation_analysis": {
                "s3_uri": "https://s3.us-east-1.amazonaws.com/victor.kim-temporary/hackathon/carenity.pdf"
            }  # 유효한 URI (처리 예상)
        }
        
        # 각 분석 실행
        video_result = video_analysis.invoke(inputs["video_analysis"])
        document_result = document_analysis.invoke(inputs["document_analysis"])
        presentation_result = presentation_analysis.invoke(inputs["presentation_analysis"])
        
        # 결과 검증
        assert video_result["status"] == "skipped"
        assert document_result["status"] == "skipped"
        assert presentation_result["status"] in ["completed", "error"]  # 처리 시도됨
        
        # 통합 결과 구성 (main.py와 유사)
        analysis_results = {
            "video_analysis": video_result,
            "document_analysis": document_result,
            "presentation_analysis": presentation_result
        }
        
        # 유효한 분석 결과 확인
        valid_results = [
            result for result in analysis_results.values()
            if result.get("status") != "skipped"
        ]
        
        # 최소 하나의 유효한 결과가 있어야 함 (presentation)
        assert len(valid_results) >= 1
    
    def test_all_empty_scenario(self):
        """모든 입력이 비어있는 시나리오 테스트"""
        document_analysis = DocumentAnalysis()
        presentation_analysis = PresentationAnalysis()
        video_analysis = VideoAnalysis()
        
        empty_input = {"s3_uri": ""}
        
        video_result = video_analysis.invoke(empty_input)
        document_result = document_analysis.invoke(empty_input)
        presentation_result = presentation_analysis.invoke(empty_input)
        
        # 모든 결과가 스킵되어야 함
        assert video_result["status"] == "skipped"
        assert document_result["status"] == "skipped"
        assert presentation_result["status"] == "skipped"
        
        # 이 경우 main.py에서 기본 데이터를 사용해야 함
        all_skipped = all(
            result["status"] == "skipped"
            for result in [video_result, document_result, presentation_result]
        )
        assert all_skipped


if __name__ == "__main__":
    pytest.main([__file__, "-v"])