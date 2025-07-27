# -*- coding: utf-8 -*-
"""
UserEngagementChain 단위 테스트
"""
import pytest
from unittest.mock import Mock
from src.chain.user_engagement_chain import UserEngagementChain


class TestUserEngagementChain:
    """UserEngagementChain 테스트 클래스"""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM 객체 생성"""
        llm = Mock()
        llm.invoke.return_value = Mock()
        return llm
    
    @pytest.fixture
    def engagement_chain(self, mock_llm):
        """UserEngagementChain 인스턴스 생성"""
        chain = UserEngagementChain(mock_llm)
        chain.output_parser = Mock()
        return chain
    
    @pytest.fixture
    def sample_input_data(self):
        """테스트용 샘플 입력 데이터"""
        return {
            "parsed_data": {
                "project_name": "인터랙티브 학습 게임",
                "description": "게임화를 통한 재미있는 학습 경험",
                "technology": "Unity, AR, 게임엔진",
                "target_users": "초중고생",
                "business_model": "앱 내 구매"
            },
            "classification": "vitamin",
            "material_analysis": "게임 요소를 통한 학습 동기 부여 및 참여도 향상"
        }
    
    def test_initialization(self, mock_llm):
        """UserEngagementChain 초기화 테스트"""
        chain = UserEngagementChain(mock_llm)
        
        assert chain.llm == mock_llm
        assert chain.chain_name == "UserEngagementChain"
        assert chain.output_parser is not None
        assert hasattr(chain, 'pain_killer_criteria')
        assert hasattr(chain, 'vitamin_criteria')
    
    def test_analyze_with_valid_response(self, engagement_chain, sample_input_data):
        """유효한 LLM 응답으로 분석 테스트"""
        mock_response = Mock()
        llm_response_text = '''
        {
            "score": 8.0,
            "reasoning": "게임화 요소가 학습 참여도를 크게 향상시킴",
            "suggestions": [
                "개인화된 학습 경로 제공",
                "소셜 기능 강화",
                "성취 시스템 개선"
            ],
            "engagement_metrics": {
                "user_experience": 8.5,
                "interaction_design": 8.0,
                "retention_potential": 7.5,
                "satisfaction_level": 8.0
            },
            "strengths": ["높은 재미 요소", "직관적 인터페이스"],
            "weaknesses": ["학습 효과 검증 필요", "연령대별 차별화 부족"],
            "engagement_aspects": {
                "pain_killer_score": 6.0,
                "vitamin_score": 8.5,
                "usability": 8.0,
                "enjoyment": 8.5,
                "stickiness": 7.5
            }
        }
        '''
        engagement_chain.llm.invoke.return_value = mock_response
        engagement_chain.output_parser.invoke.return_value = llm_response_text
        
        result = engagement_chain._analyze(sample_input_data)
        
        assert result["score"] == 8.0
        assert "참여도를 크게 향상" in result["reasoning"]
        assert len(result["suggestions"]) == 3
        # 기본 필드들만 확인 (실제 구현에 따라 다를 수 있음)
        assert "score" in result
        assert "reasoning" in result
        assert "suggestions" in result
    
    def test_base_class_interface_compliance(self, engagement_chain):
        """베이스 클래스 인터페이스 준수 테스트"""
        result = engagement_chain.invoke({})
        
        required_fields = ['score', 'reasoning', 'suggestions', 'execution_time', 'chain_name']
        for field in required_fields:
            assert field in result, f"필수 필드 {field}가 결과에 없음"
        
        assert result['chain_name'] == 'UserEngagementChain'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])