# -*- coding: utf-8 -*-
"""
NetworkEffectChain 단위 테스트
"""
import pytest
from unittest.mock import Mock
from src.chain.network_effect_chain import NetworkEffectChain


class TestNetworkEffectChain:
    """NetworkEffectChain 테스트 클래스"""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM 객체 생성"""
        llm = Mock()
        llm.invoke.return_value = Mock()
        return llm
    
    @pytest.fixture
    def network_chain(self, mock_llm):
        """NetworkEffectChain 인스턴스 생성"""
        chain = NetworkEffectChain(mock_llm)
        chain.output_parser = Mock()
        return chain
    
    @pytest.fixture
    def sample_input_data(self):
        """테스트용 샘플 입력 데이터"""
        return {
            "parsed_data": {
                "project_name": "소셜 학습 플랫폼",
                "description": "사용자 간 지식 공유 및 협업 학습",
                "technology": "React, Node.js, WebRTC",
                "target_users": "학생, 교육자",
                "business_model": "프리미엄 구독"
            },
            "classification": "vitamin",
            "material_analysis": "사용자 간 상호작용을 통한 학습 효과 증대"
        }
    
    def test_initialization(self, mock_llm):
        """NetworkEffectChain 초기화 테스트"""
        chain = NetworkEffectChain(mock_llm)
        
        assert chain.llm == mock_llm
        assert chain.chain_name == "NetworkEffectChain"
        assert chain.output_parser is not None
        assert hasattr(chain, 'pain_killer_criteria')
        assert hasattr(chain, 'vitamin_criteria')
    
    def test_analyze_with_valid_response(self, network_chain, sample_input_data):
        """유효한 LLM 응답으로 분석 테스트"""
        mock_response = Mock()
        llm_response_text = '''
        {
            "score": 8.5,
            "reasoning": "사용자 간 상호작용이 활발하고 네트워크 효과가 강함",
            "suggestions": [
                "바이럴 기능 강화",
                "사용자 인센티브 시스템 도입",
                "커뮤니티 기능 확대"
            ],
            "network_analysis": {
                "user_interaction_potential": 8.0,
                "viral_growth_potential": 7.5,
                "platform_stickiness": 8.5,
                "network_density": 7.0
            },
            "strengths": ["강한 사용자 참여", "자연스러운 바이럴 확산"],
            "limitations": ["초기 사용자 확보", "네트워크 임계점 도달"],
            "network_aspects": {
                "pain_killer_score": 6.0,
                "vitamin_score": 8.5,
                "user_engagement": 8.0,
                "viral_coefficient": 7.5,
                "retention_rate": 8.0
            }
        }
        '''
        network_chain.llm.invoke.return_value = mock_response
        network_chain.output_parser.invoke.return_value = llm_response_text
        
        result = network_chain._analyze(sample_input_data)
        
        assert result["score"] == 8.5
        assert "네트워크 효과가 강함" in result["reasoning"]
        assert len(result["suggestions"]) == 3
        assert "강한 사용자 참여" in result["strengths"]
        assert "초기 사용자 확보" in result["limitations"]
        assert result["network_analysis"]["viral_growth_potential"] == 7.5
        assert result["network_aspects"]["vitamin_score"] == 8.5
    
    def test_analyze_with_invalid_json(self, network_chain, sample_input_data):
        """잘못된 JSON 응답 처리 테스트"""
        mock_response = Mock()
        network_chain.llm.invoke.return_value = mock_response
        network_chain.output_parser.invoke.return_value = "잘못된 JSON 응답"
        
        result = network_chain._analyze(sample_input_data)
        
        assert result["score"] == 5.0
        assert "기본 점수를 제공합니다" in result["reasoning"]
        assert len(result["suggestions"]) > 0
    
    def test_validate_score(self, network_chain):
        """점수 검증 테스트"""
        assert network_chain._validate_score(7.5) == 7.5
        assert network_chain._validate_score("8.2") == 8.2
        assert network_chain._validate_score(15.0) == 10.0
        assert network_chain._validate_score(-2.0) == 0.0
        assert network_chain._validate_score("invalid") == 5.0
        assert network_chain._validate_score(None) == 5.0
    
    def test_invoke_method(self, network_chain, sample_input_data):
        """invoke 메서드 테스트 (베이스 클래스 상속 확인)"""
        mock_response = Mock()
        llm_response_text = '''
        {
            "score": 7.0,
            "reasoning": "네트워크 효과 분석 완료",
            "suggestions": ["개선 제안"]
        }
        '''
        network_chain.llm.invoke.return_value = mock_response
        network_chain.output_parser.invoke.return_value = llm_response_text
        
        result = network_chain.invoke(sample_input_data)
        
        # 표준화된 결과 형식 확인
        assert "score" in result
        assert "reasoning" in result
        assert "suggestions" in result
        assert "execution_time" in result
        assert "chain_name" in result
        assert result["chain_name"] == "NetworkEffectChain"
    
    def test_base_class_interface_compliance(self, network_chain):
        """베이스 클래스 인터페이스 준수 테스트"""
        assert hasattr(network_chain, 'invoke')
        assert hasattr(network_chain, '_analyze')
        assert hasattr(network_chain, 'chain_name')
        assert hasattr(network_chain, 'logger')
        
        result = network_chain.invoke({})
        
        required_fields = ['score', 'reasoning', 'suggestions', 'execution_time', 'chain_name']
        for field in required_fields:
            assert field in result, f"필수 필드 {field}가 결과에 없음"
        
        assert isinstance(result['score'], (int, float))
        assert isinstance(result['reasoning'], str)
        assert isinstance(result['suggestions'], list)
        assert isinstance(result['execution_time'], (int, float))
        assert isinstance(result['chain_name'], str)
        assert result['chain_name'] == 'NetworkEffectChain'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])