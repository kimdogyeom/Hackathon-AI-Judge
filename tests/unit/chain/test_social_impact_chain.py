# -*- coding: utf-8 -*-
"""
SocialImpactChain 단위 테스트
"""
import pytest
from unittest.mock import Mock
from src.chain.social_impact_chain import SocialImpactChain


class TestSocialImpactChain:
    """SocialImpactChain 테스트 클래스"""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM 객체 생성"""
        llm = Mock()
        llm.invoke.return_value = Mock()
        return llm
    
    @pytest.fixture
    def social_chain(self, mock_llm):
        """SocialImpactChain 인스턴스 생성"""
        chain = SocialImpactChain(mock_llm)
        chain.output_parser = Mock()
        return chain
    
    @pytest.fixture
    def sample_input_data(self):
        """테스트용 샘플 입력 데이터"""
        return {
            "parsed_data": {
                "project_name": "장애인 접근성 향상 앱",
                "description": "시각 장애인을 위한 음성 네비게이션",
                "technology": "AI, 음성인식, GPS",
                "target_users": "시각 장애인",
                "business_model": "공익 서비스"
            },
            "classification": "painkiller",
            "material_analysis": "사회적 약자를 위한 접근성 개선 솔루션"
        }
    
    def test_initialization(self, mock_llm):
        """SocialImpactChain 초기화 테스트"""
        chain = SocialImpactChain(mock_llm)
        
        assert chain.llm == mock_llm
        assert chain.chain_name == "SocialImpactChain"
        assert chain.output_parser is not None
        assert hasattr(chain, 'pain_killer_criteria')
        assert hasattr(chain, 'vitamin_criteria')
    
    def test_analyze_with_valid_response(self, social_chain, sample_input_data):
        """유효한 LLM 응답으로 분석 테스트"""
        mock_response = Mock()
        llm_response_text = '''
        {
            "score": 9.0,
            "reasoning": "시각 장애인의 이동권 보장에 큰 기여",
            "suggestions": [
                "다양한 장애 유형 지원 확대",
                "지역 커뮤니티와 연계",
                "정부 지원 프로그램 활용"
            ],
            "impact_areas": {
                "accessibility": 9.5,
                "inclusion": 8.5,
                "equality": 9.0,
                "community_benefit": 8.0
            },
            "strengths": ["직접적인 사회 문제 해결", "취약계층 지원"],
            "limitations": ["제한된 사용자층", "수익성 부족"],
            "social_aspects": {
                "pain_killer_score": 9.0,
                "vitamin_score": 6.0,
                "problem_severity": 9.0,
                "solution_effectiveness": 8.5,
                "scalability": 7.0
            }
        }
        '''
        social_chain.llm.invoke.return_value = mock_response
        social_chain.output_parser.invoke.return_value = llm_response_text
        
        result = social_chain._analyze(sample_input_data)
        
        assert result["score"] == 9.0
        assert "이동권 보장" in result["reasoning"]
        assert len(result["suggestions"]) == 3
        # 기본 필드들만 확인 (실제 구현에 따라 다를 수 있음)
        assert "score" in result
        assert "reasoning" in result
        assert "suggestions" in result
    
    def test_base_class_interface_compliance(self, social_chain):
        """베이스 클래스 인터페이스 준수 테스트"""
        result = social_chain.invoke({})
        
        required_fields = ['score', 'reasoning', 'suggestions', 'execution_time', 'chain_name']
        for field in required_fields:
            assert field in result, f"필수 필드 {field}가 결과에 없음"
        
        assert result['chain_name'] == 'SocialImpactChain'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])