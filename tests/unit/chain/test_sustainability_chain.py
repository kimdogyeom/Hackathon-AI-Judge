# -*- coding: utf-8 -*-
"""
SustainabilityChain 단위 테스트
"""
import pytest
from unittest.mock import Mock
from src.chain.sustainability_chain import SustainabilityChain


class TestSustainabilityChain:
    """SustainabilityChain 테스트 클래스"""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM 객체 생성"""
        llm = Mock()
        llm.invoke.return_value = Mock()
        return llm
    
    @pytest.fixture
    def sustainability_chain(self, mock_llm):
        """SustainabilityChain 인스턴스 생성"""
        chain = SustainabilityChain(mock_llm)
        chain.output_parser = Mock()
        return chain
    
    @pytest.fixture
    def sample_input_data(self):
        """테스트용 샘플 입력 데이터"""
        return {
            "parsed_data": {
                "project_name": "친환경 에너지 관리 시스템",
                "description": "태양광 에너지 최적화 및 탄소 배출 감소",
                "technology": "IoT, AI, 재생에너지",
                "target_users": "기업, 가정",
                "business_model": "에너지 절약 수수료"
            },
            "classification": "painkiller",
            "material_analysis": "환경 문제 해결과 에너지 효율성 개선"
        }
    
    def test_initialization(self, mock_llm):
        """SustainabilityChain 초기화 테스트"""
        chain = SustainabilityChain(mock_llm)
        
        assert chain.llm == mock_llm
        assert chain.chain_name == "SustainabilityChain"
        assert chain.output_parser is not None
        assert hasattr(chain, 'pain_killer_criteria')
        assert hasattr(chain, 'vitamin_criteria')
    
    def test_analyze_with_valid_response(self, sustainability_chain, sample_input_data):
        """유효한 LLM 응답으로 분석 테스트"""
        mock_response = Mock()
        llm_response_text = '''
        {
            "score": 8.5,
            "reasoning": "탄소 배출 감소와 에너지 효율성 크게 개선",
            "suggestions": [
                "재생에너지 비율 확대",
                "에너지 저장 기술 도입",
                "탄소 크레딧 시스템 연계"
            ],
            "sustainability_metrics": {
                "environmental_impact": 9.0,
                "resource_efficiency": 8.0,
                "carbon_reduction": 8.5,
                "renewable_energy": 7.5
            },
            "strengths": ["직접적인 환경 개선", "경제적 효과"],
            "challenges": ["초기 투자 비용", "기술 복잡성"],
            "sustainability_aspects": {
                "pain_killer_score": 8.5,
                "vitamin_score": 7.0,
                "environmental_benefit": 9.0,
                "economic_viability": 7.5,
                "long_term_impact": 8.5
            }
        }
        '''
        sustainability_chain.llm.invoke.return_value = mock_response
        sustainability_chain.output_parser.invoke.return_value = llm_response_text
        
        result = sustainability_chain._analyze(sample_input_data)
        
        assert result["score"] == 8.5
        assert "탄소 배출 감소" in result["reasoning"]
        assert len(result["suggestions"]) == 3
        # 기본 필드들만 확인 (실제 구현에 따라 다를 수 있음)
        assert "score" in result
        assert "reasoning" in result
        assert "suggestions" in result
    
    def test_base_class_interface_compliance(self, sustainability_chain):
        """베이스 클래스 인터페이스 준수 테스트"""
        result = sustainability_chain.invoke({})
        
        required_fields = ['score', 'reasoning', 'suggestions', 'execution_time', 'chain_name']
        for field in required_fields:
            assert field in result, f"필수 필드 {field}가 결과에 없음"
        
        assert result['chain_name'] == 'SustainabilityChain'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])