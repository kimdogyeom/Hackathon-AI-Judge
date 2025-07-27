# -*- coding: utf-8 -*-
"""
TechnicalFeasibilityChain 단위 테스트
"""
import pytest
from unittest.mock import Mock
from src.chain.technical_feasibility_chain import TechnicalFeasibilityChain


class TestTechnicalFeasibilityChain:
    """TechnicalFeasibilityChain 테스트 클래스"""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM 객체 생성"""
        llm = Mock()
        llm.invoke.return_value = Mock()
        return llm
    
    @pytest.fixture
    def technical_chain(self, mock_llm):
        """TechnicalFeasibilityChain 인스턴스 생성"""
        chain = TechnicalFeasibilityChain(mock_llm)
        chain.output_parser = Mock()
        return chain
    
    @pytest.fixture
    def sample_input_data(self):
        """테스트용 샘플 입력 데이터"""
        return {
            "parsed_data": {
                "project_name": "블록체인 기반 투표 시스템",
                "description": "투명하고 안전한 전자 투표 플랫폼",
                "technology": "Blockchain, Cryptography, Web3",
                "target_users": "정부, 기관",
                "business_model": "라이선스 판매"
            },
            "classification": "painkiller",
            "material_analysis": "기존 투표 시스템의 보안 및 투명성 문제 해결"
        }
    
    def test_initialization(self, mock_llm):
        """TechnicalFeasibilityChain 초기화 테스트"""
        chain = TechnicalFeasibilityChain(mock_llm)
        
        assert chain.llm == mock_llm
        assert chain.chain_name == "TechnicalFeasibilityChain"
        assert chain.output_parser is not None
        assert hasattr(chain, 'pain_killer_criteria')
        assert hasattr(chain, 'vitamin_criteria')
    
    def test_analyze_with_valid_response(self, technical_chain, sample_input_data):
        """유효한 LLM 응답으로 분석 테스트"""
        mock_response = Mock()
        llm_response_text = '''
        {
            "score": 7.5,
            "reasoning": "블록체인 기술은 성숙하나 대규모 구현에 도전 과제 존재",
            "suggestions": [
                "확장성 솔루션 도입",
                "사용자 친화적 인터페이스 개발",
                "규제 준수 방안 마련"
            ],
            "technical_metrics": {
                "implementation_complexity": 8.0,
                "technology_maturity": 7.0,
                "scalability": 6.5,
                "security_level": 9.0
            },
            "strengths": ["높은 보안성", "투명성 보장"],
            "risks": ["확장성 제한", "규제 불확실성"],
            "feasibility_aspects": {
                "pain_killer_score": 8.0,
                "vitamin_score": 6.0,
                "technical_difficulty": 7.5,
                "resource_requirement": 8.0,
                "timeline_feasibility": 6.5
            }
        }
        '''
        technical_chain.llm.invoke.return_value = mock_response
        technical_chain.output_parser.invoke.return_value = llm_response_text
        
        result = technical_chain._analyze(sample_input_data)
        
        assert result["score"] == 7.5
        assert "블록체인 기술" in result["reasoning"]
        assert len(result["suggestions"]) == 3
        # 기본 필드들만 확인 (실제 구현에 따라 다를 수 있음)
        assert "score" in result
        assert "reasoning" in result
        assert "suggestions" in result
    
    def test_base_class_interface_compliance(self, technical_chain):
        """베이스 클래스 인터페이스 준수 테스트"""
        result = technical_chain.invoke({})
        
        required_fields = ['score', 'reasoning', 'suggestions', 'execution_time', 'chain_name']
        for field in required_fields:
            assert field in result, f"필수 필드 {field}가 결과에 없음"
        
        assert result['chain_name'] == 'TechnicalFeasibilityChain'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])