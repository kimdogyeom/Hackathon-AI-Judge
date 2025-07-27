# -*- coding: utf-8 -*-
"""
CostAnalysisChain 단위 테스트
"""
import pytest
from unittest.mock import Mock, patch
from src.chain.cost_analysis_chain import CostAnalysisChain


class TestCostAnalysisChain:
    """CostAnalysisChain 테스트 클래스"""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM 객체 생성"""
        llm = Mock()
        llm.invoke.return_value = Mock()
        return llm
    
    @pytest.fixture
    def cost_chain(self, mock_llm):
        """CostAnalysisChain 인스턴스 생성"""
        chain = CostAnalysisChain(mock_llm)
        chain.output_parser = Mock()
        return chain
    
    @pytest.fixture
    def sample_input_data(self):
        """테스트용 샘플 입력 데이터"""
        return {
            "parsed_data": {
                "project_name": "스마트 재고 관리 시스템",
                "description": "AI 기반 재고 최적화로 비용 절감",
                "technology": "Python, AI, 클라우드",
                "target_users": "중소기업",
                "business_model": "SaaS 구독"
            },
            "classification": "painkiller",
            "material_analysis": "재고 관리 비용 절감에 중점을 둔 솔루션"
        }
    
    def test_initialization(self, mock_llm):
        """CostAnalysisChain 초기화 테스트"""
        chain = CostAnalysisChain(mock_llm)
        
        assert chain.llm == mock_llm
        assert chain.chain_name == "CostAnalysisChain"
        assert chain.output_parser is not None
        assert hasattr(chain, 'pain_killer_criteria')
        assert hasattr(chain, 'vitamin_criteria')
    
    def test_analyze_with_valid_response(self, cost_chain, sample_input_data):
        """유효한 LLM 응답으로 분석 테스트"""
        mock_response = Mock()
        llm_response_text = '''
        {
            "score": 8.0,
            "reasoning": "재고 관리 비용을 30% 절감하는 효과적인 솔루션",
            "suggestions": [
                "클라우드 비용 최적화",
                "개발 리소스 효율화",
                "수익 모델 다각화"
            ],
            "cost_breakdown": {
                "development_cost": "초기 개발비 1억원 예상",
                "operational_cost": "월 운영비 500만원",
                "expected_revenue": "월 매출 2000만원 예상",
                "roi_estimate": "12개월 내 투자 회수"
            },
            "strengths": ["높은 비용 절감 효과", "빠른 ROI"],
            "risks": ["초기 투자 부담", "시장 경쟁"],
            "cost_aspects": {
                "pain_killer_score": 8.5,
                "vitamin_score": 6.0,
                "development_efficiency": 7.5,
                "operational_efficiency": 8.0,
                "roi_potential": 8.5
            }
        }
        '''
        cost_chain.llm.invoke.return_value = mock_response
        cost_chain.output_parser.invoke.return_value = llm_response_text
        
        result = cost_chain._analyze(sample_input_data)
        
        assert result["score"] == 8.0
        assert "30% 절감" in result["reasoning"]
        assert len(result["suggestions"]) == 3
        assert "높은 비용 절감 효과" in result["strengths"]
        assert "초기 투자 부담" in result["risks"]
        assert result["cost_breakdown"]["roi_estimate"] == "12개월 내 투자 회수"
        assert result["cost_aspects"]["roi_potential"] == 8.5
    
    def test_analyze_with_invalid_json(self, cost_chain, sample_input_data):
        """잘못된 JSON 응답 처리 테스트"""
        mock_response = Mock()
        cost_chain.llm.invoke.return_value = mock_response
        cost_chain.output_parser.invoke.return_value = "잘못된 JSON 응답"
        
        result = cost_chain._analyze(sample_input_data)
        
        assert result["score"] == 5.0
        assert "기본 점수를 제공합니다" in result["reasoning"]
        assert len(result["suggestions"]) > 0
        assert "cost_breakdown" in result
    
    def test_analyze_with_missing_data(self, cost_chain):
        """데이터 부족 상황 테스트"""
        incomplete_data = {
            "parsed_data": {
                "project_name": "테스트 프로젝트"
            },
            "classification": "vitamin"
        }
        
        mock_response = Mock()
        llm_response_text = '''
        {
            "score": 6.0,
            "reasoning": "제한된 정보로 인한 평가",
            "suggestions": ["더 많은 비용 정보 필요"]
        }
        '''
        cost_chain.llm.invoke.return_value = mock_response
        cost_chain.output_parser.invoke.return_value = llm_response_text
        
        result = cost_chain._analyze(incomplete_data)
        
        assert "data_limitations" in result
        assert "자료 부족" in result["data_limitations"]
    
    def test_validate_score(self, cost_chain):
        """점수 검증 테스트"""
        assert cost_chain._validate_score(7.5) == 7.5
        assert cost_chain._validate_score("8.2") == 8.2
        assert cost_chain._validate_score(15.0) == 10.0
        assert cost_chain._validate_score(-2.0) == 0.0
        assert cost_chain._validate_score("invalid") == 5.0
        assert cost_chain._validate_score(None) == 5.0
    
    def test_validate_and_normalize_result(self, cost_chain):
        """결과 검증 및 정규화 테스트"""
        raw_result = {
            "score": 8.5,
            "reasoning": "좋은 비용 효율성",
            "suggestions": ["제안1", "제안2"],
            "cost_breakdown": {"development_cost": "1억원"},
            "strengths": ["강점1"],
            "risks": ["리스크1"],
            "cost_aspects": {"roi_potential": 8.0}
        }
        
        normalized = cost_chain._validate_and_normalize_result(raw_result)
        
        assert normalized["score"] == 8.5
        assert normalized["reasoning"] == "좋은 비용 효율성"
        assert normalized["suggestions"] == ["제안1", "제안2"]
        assert "cost_breakdown" in normalized
        assert "strengths" in normalized
        assert "risks" in normalized
        assert "cost_aspects" in normalized
    
    def test_invoke_method(self, cost_chain, sample_input_data):
        """invoke 메서드 테스트 (베이스 클래스 상속 확인)"""
        mock_response = Mock()
        llm_response_text = '''
        {
            "score": 7.0,
            "reasoning": "비용 효율적인 솔루션",
            "suggestions": ["개선 제안"]
        }
        '''
        cost_chain.llm.invoke.return_value = mock_response
        cost_chain.output_parser.invoke.return_value = llm_response_text
        
        result = cost_chain.invoke(sample_input_data)
        
        # 표준화된 결과 형식 확인
        assert "score" in result
        assert "reasoning" in result
        assert "suggestions" in result
        assert "execution_time" in result
        assert "chain_name" in result
        assert result["chain_name"] == "CostAnalysisChain"
    
    def test_call_method_compatibility(self, cost_chain, sample_input_data):
        """기존 __call__ 메서드 호환성 테스트"""
        mock_response = Mock()
        llm_response_text = '''
        {
            "score": 6.5,
            "reasoning": "테스트 평가",
            "suggestions": ["테스트 제안"]
        }
        '''
        cost_chain.llm.invoke.return_value = mock_response
        cost_chain.output_parser.invoke.return_value = llm_response_text
        
        result = cost_chain(sample_input_data)
        
        assert isinstance(result, dict)
        assert "score" in result
        assert result["score"] == 6.5
    
    def test_run_method_compatibility(self, cost_chain):
        """기존 run 메서드 호환성 테스트"""
        mock_response = Mock()
        llm_response_text = '''
        {
            "score": 7.8,
            "reasoning": "run 메서드 테스트",
            "suggestions": ["테스트"]
        }
        '''
        cost_chain.llm.invoke.return_value = mock_response
        cost_chain.output_parser.invoke.return_value = llm_response_text
        
        score = cost_chain.run()
        
        assert isinstance(score, (int, float))
        assert score == 7.8
    
    def test_data_limitations_check(self, cost_chain):
        """데이터 제한사항 확인 테스트"""
        complete_data = {
            "video_analysis": {"content": "비디오 내용"},
            "document_analysis": {"content": "문서 내용"},
            "presentation_analysis": {"content": "발표자료 내용"}
        }
        limitations = cost_chain._check_data_availability(complete_data)
        assert len(limitations) == 0
        
        incomplete_data = {
            "video_analysis": {"content": "비디오 내용"},
            "document_analysis": {},
            "presentation_analysis": {"content": ""}
        }
        limitations = cost_chain._check_data_availability(incomplete_data)
        assert len(limitations) == 2
        assert any("문서 자료 부족" in limitation for limitation in limitations)
        assert any("발표자료 부족" in limitation for limitation in limitations)
    
    def test_as_runnable(self, cost_chain):
        """as_runnable 메서드 테스트"""
        runnable = cost_chain.as_runnable()
        assert runnable == cost_chain
    
    def test_fallback_result(self, cost_chain):
        """fallback 결과 테스트"""
        limitations = ["비디오 자료 부족", "문서 자료 부족"]
        result = cost_chain._get_fallback_result(limitations)
        
        assert result["score"] == 5.0
        assert "기본 점수를 제공합니다" in result["reasoning"]
        assert len(result["suggestions"]) > 0
        assert "cost_breakdown" in result
        assert "data_limitations" in result
        assert "비디오 자료 부족" in result["data_limitations"]
    
    def test_base_class_interface_compliance(self, cost_chain):
        """베이스 클래스 인터페이스 준수 테스트"""
        assert hasattr(cost_chain, 'invoke')
        assert hasattr(cost_chain, '_analyze')
        assert hasattr(cost_chain, 'chain_name')
        assert hasattr(cost_chain, 'logger')
        
        result = cost_chain.invoke({})
        
        required_fields = ['score', 'reasoning', 'suggestions', 'execution_time', 'chain_name']
        for field in required_fields:
            assert field in result, f"필수 필드 {field}가 결과에 없음"
        
        assert isinstance(result['score'], (int, float))
        assert isinstance(result['reasoning'], str)
        assert isinstance(result['suggestions'], list)
        assert isinstance(result['execution_time'], (int, float))
        assert isinstance(result['chain_name'], str)
        assert result['chain_name'] == 'CostAnalysisChain'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])