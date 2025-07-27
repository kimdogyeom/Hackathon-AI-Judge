# -*- coding: utf-8 -*-
import pytest
from unittest.mock import Mock, patch
from src.chain.innovation_chain import InnovationChain


class TestInnovationChain:
    """InnovationChain 테스트 클래스"""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM 객체 생성"""
        llm = Mock()
        llm.invoke.return_value = Mock()
        return llm
    
    @pytest.fixture
    def innovation_chain(self, mock_llm):
        """InnovationChain 인스턴스 생성"""
        chain = InnovationChain(mock_llm)
        # output_parser를 Mock으로 교체
        chain.output_parser = Mock()
        return chain
    
    @pytest.fixture
    def sample_input_data(self):
        """테스트용 샘플 입력 데이터"""
        return {
            "parsed_data": {
                "project_name": "AI 기반 스마트 농업 시스템",
                "description": "IoT 센서와 AI를 활용한 자동화된 농업 관리 시스템",
                "technology": "Python, TensorFlow, IoT, 클라우드",
                "target_users": "농업인, 농업 기업",
                "business_model": "SaaS 구독 모델"
            },
            "classification": "painkiller",
            "material_analysis": "농업 생산성 향상과 비용 절감에 중점을 둔 혁신적인 솔루션",
            "video_analysis": {"content": "비디오 분석 내용"},
            "document_analysis": {"content": "문서 분석 내용"},
            "presentation_analysis": {"content": "발표자료 분석 내용"}
        }
    
    def test_initialization(self, mock_llm):
        """InnovationChain 초기화 테스트"""
        chain = InnovationChain(mock_llm)
        
        assert chain.llm == mock_llm
        assert chain.chain_name == "InnovationChain"
        assert chain.output_parser is not None
        assert hasattr(chain, 'pain_killer_criteria')
        assert hasattr(chain, 'vitamin_criteria')
    
    def test_analyze_with_valid_response(self, innovation_chain, sample_input_data):
        """유효한 LLM 응답으로 분석 테스트"""
        # Mock LLM 응답 설정
        mock_response = Mock()
        llm_response_text = '''
        {
            "score": 8.5,
            "reasoning": "IoT와 AI를 결합한 혁신적인 농업 솔루션으로 기술적 참신성이 높음",
            "suggestions": [
                "더 다양한 작물에 대한 AI 모델 개발",
                "농업인 교육 프로그램 추가",
                "데이터 보안 강화"
            ],
            "strengths": ["기술적 혁신성", "실용적 가치"],
            "weaknesses": ["초기 도입 비용", "기술 복잡성"],
            "innovation_aspects": {
                "idea_originality": 8.0,
                "technical_novelty": 9.0,
                "creative_approach": 8.0,
                "market_innovation": 7.5,
                "value_creation": 8.5
            }
        }
        '''
        innovation_chain.llm.invoke.return_value = mock_response
        innovation_chain.output_parser.invoke.return_value = llm_response_text
        
        # 분석 실행
        result = innovation_chain._analyze(sample_input_data)
        
        # 결과 검증
        assert result["score"] == 8.5
        assert "IoT와 AI를 결합한" in result["reasoning"]
        assert len(result["suggestions"]) == 3
        assert "기술적 혁신성" in result["strengths"]
        assert "초기 도입 비용" in result["weaknesses"]
        assert result["innovation_aspects"]["technical_novelty"] == 9.0
    
    def test_analyze_with_invalid_json(self, innovation_chain, sample_input_data):
        """잘못된 JSON 응답 처리 테스트"""
        # Mock LLM 응답 설정 (잘못된 JSON)
        mock_response = Mock()
        innovation_chain.llm.invoke.return_value = mock_response
        innovation_chain.output_parser.invoke.return_value = "잘못된 JSON 응답"
        
        # 분석 실행
        result = innovation_chain._analyze(sample_input_data)
        
        # 기본값 반환 확인
        assert result["score"] == 5.0
        assert "기본 점수를 제공합니다" in result["reasoning"]
        assert len(result["suggestions"]) > 0
    
    def test_analyze_with_missing_data(self, innovation_chain):
        """데이터 부족 상황 테스트"""
        incomplete_data = {
            "parsed_data": {
                "project_name": "테스트 프로젝트"
            },
            "classification": "vitamin"
        }
        
        # Mock LLM 응답 설정
        mock_response = Mock()
        llm_response_text = '''
        {
            "score": 6.0,
            "reasoning": "제한된 정보로 인한 평가",
            "suggestions": ["더 많은 정보 제공 필요"]
        }
        '''
        innovation_chain.llm.invoke.return_value = mock_response
        innovation_chain.output_parser.invoke.return_value = llm_response_text
        
        # 분석 실행
        result = innovation_chain._analyze(incomplete_data)
        
        # 데이터 제한사항 확인
        assert "data_limitations" in result
        assert "자료 부족" in result["data_limitations"]
    
    def test_validate_score(self, innovation_chain):
        """점수 검증 테스트"""
        # 유효한 점수
        assert innovation_chain._validate_score(7.5) == 7.5
        assert innovation_chain._validate_score("8.2") == 8.2
        
        # 범위 초과 점수
        assert innovation_chain._validate_score(15.0) == 10.0
        assert innovation_chain._validate_score(-2.0) == 0.0
        
        # 잘못된 타입
        assert innovation_chain._validate_score("invalid") == 5.0
        assert innovation_chain._validate_score(None) == 5.0
    
    def test_validate_and_normalize_result(self, innovation_chain):
        """결과 검증 및 정규화 테스트"""
        raw_result = {
            "score": 8.5,
            "reasoning": "좋은 혁신성",
            "improvement_suggestions": ["제안1", "제안2"],  # 이전 형식
            "strengths": ["강점1"],
            "weaknesses": ["약점1"]
        }
        
        normalized = innovation_chain._validate_and_normalize_result(raw_result)
        
        assert normalized["score"] == 8.5
        assert normalized["reasoning"] == "좋은 혁신성"
        assert normalized["suggestions"] == ["제안1", "제안2"]  # 새 형식으로 변환
        assert "strengths" in normalized
        assert "weaknesses" in normalized
    
    def test_invoke_method(self, innovation_chain, sample_input_data):
        """invoke 메서드 테스트 (베이스 클래스 상속 확인)"""
        # Mock LLM 응답 설정
        mock_response = Mock()
        llm_response_text = '''
        {
            "score": 7.0,
            "reasoning": "혁신적인 아이디어",
            "suggestions": ["개선 제안"]
        }
        '''
        innovation_chain.llm.invoke.return_value = mock_response
        innovation_chain.output_parser.invoke.return_value = llm_response_text
        
        # invoke 실행
        result = innovation_chain.invoke(sample_input_data)
        
        # 표준화된 결과 형식 확인
        assert "score" in result
        assert "reasoning" in result
        assert "suggestions" in result
        assert "execution_time" in result
        assert "chain_name" in result
        assert result["chain_name"] == "InnovationChain"
    
    def test_call_method_compatibility(self, innovation_chain, sample_input_data):
        """기존 __call__ 메서드 호환성 테스트"""
        # Mock LLM 응답 설정
        mock_response = Mock()
        llm_response_text = '''
        {
            "score": 6.5,
            "reasoning": "테스트 평가",
            "suggestions": ["테스트 제안"]
        }
        '''
        innovation_chain.llm.invoke.return_value = mock_response
        innovation_chain.output_parser.invoke.return_value = llm_response_text
        
        # __call__ 실행
        result = innovation_chain(sample_input_data)
        
        # 결과 확인
        assert isinstance(result, dict)
        assert "score" in result
        assert result["score"] == 6.5
    
    def test_run_method_compatibility(self, innovation_chain):
        """기존 run 메서드 호환성 테스트"""
        # Mock LLM 응답 설정
        mock_response = Mock()
        llm_response_text = '''
        {
            "score": 7.8,
            "reasoning": "run 메서드 테스트",
            "suggestions": ["테스트"]
        }
        '''
        innovation_chain.llm.invoke.return_value = mock_response
        innovation_chain.output_parser.invoke.return_value = llm_response_text
        
        # run 실행
        score = innovation_chain.run()
        
        # 점수만 반환하는지 확인
        assert isinstance(score, (int, float))
        assert score == 7.8
    
    def test_data_limitations_check(self, innovation_chain):
        """데이터 제한사항 확인 테스트"""
        # 모든 데이터가 있는 경우
        complete_data = {
            "video_analysis": {"content": "비디오 내용"},
            "document_analysis": {"content": "문서 내용"},
            "presentation_analysis": {"content": "발표자료 내용"}
        }
        limitations = innovation_chain._check_data_availability(complete_data)
        assert len(limitations) == 0
        
        # 일부 데이터가 없는 경우
        incomplete_data = {
            "video_analysis": {"content": "비디오 내용"},
            "document_analysis": {},  # 빈 내용
            "presentation_analysis": {"content": ""}  # 빈 문자열
        }
        limitations = innovation_chain._check_data_availability(incomplete_data)
        assert len(limitations) == 2
        assert any("문서 자료 부족" in limitation for limitation in limitations)
        assert any("발표자료 부족" in limitation for limitation in limitations)
    
    def test_as_runnable(self, innovation_chain):
        """as_runnable 메서드 테스트"""
        runnable = innovation_chain.as_runnable()
        assert runnable == innovation_chain