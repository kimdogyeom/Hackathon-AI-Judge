# -*- coding: utf-8 -*-
"""
BusinessValueChain 단위 테스트
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from src.chain.business_value_chain import BusinessValueChain


class TestBusinessValueChain:
    """BusinessValueChain 클래스 테스트"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.chain = BusinessValueChain()
    
    def test_init_with_default_config(self):
        """기본 설정으로 초기화 테스트"""
        chain = BusinessValueChain()
        assert hasattr(chain, 'pain_killer_evaluation_list')
        assert hasattr(chain, 'vitamin_evaluation_list')
        assert hasattr(chain, 'llm')
    
    def test_string_input_processing(self):
        """문자열 입력 처리 테스트"""
        test_input = "AI 기반 헬스케어 시스템"
        processed = self.chain._process_input(test_input)
        assert processed == test_input
    
    def test_dict_input_processing(self):
        """딕셔너리 입력 처리 테스트"""
        test_input = {
            "title": "프로젝트 제목",
            "description": "프로젝트 설명",
            "content": "프로젝트 내용"
        }
        processed = self.chain._process_input(test_input)
        
        assert "프로젝트 제목: 프로젝트 제목" in processed
        assert "프로젝트 설명: 프로젝트 설명" in processed
        assert "내용: 프로젝트 내용" in processed
    
    def test_other_input_processing(self):
        """기타 타입 입력 처리 테스트"""
        test_input = 12345
        processed = self.chain._process_input(test_input)
        assert processed == "12345"
    
    def test_successful_evaluation(self):
        """성공적인 평가 테스트"""
        test_project = """
        프로젝트명: AI 기반 스마트 재고 관리 시스템
        
        프로젝트 설명:
        - 중소기업을 위한 IoT 센서와 AI를 활용한 실시간 재고 모니터링 시스템
        - 재고 부족으로 인한 매출 손실을 30% 감소시키고 재고 관리 비용을 25% 절감
        """
        
        result = self.chain.invoke(test_project)
        
        # 필수 필드 검증
        assert 'total_score' in result
        assert 'pain_killer_score' in result
        assert 'vitamin_score' in result
        assert 'evaluation_type' in result
        
        # 점수 범위 검증
        assert 0 <= result['total_score'] <= 10
        assert 0 <= result['pain_killer_score'] <= 10
        assert 0 <= result['vitamin_score'] <= 10
    
    def test_empty_input_handling(self):
        """빈 입력 처리 테스트"""
        result = self.chain.invoke("")
        
        # 오류 상황에서도 기본 구조 유지
        assert 'total_score' in result
        assert 'pain_killer_score' in result
        assert 'vitamin_score' in result
        assert 'evaluation_type' in result
        
        # 점수는 0 이상이어야 함
        assert result['total_score'] >= 0
    
    def test_none_input_handling(self):
        """None 입력 처리 테스트"""
        result = self.chain.invoke(None)
        
        # 오류 상황에서도 기본 구조 유지
        assert 'total_score' in result
        assert 'pain_killer_score' in result
        assert 'vitamin_score' in result
        assert 'evaluation_type' in result
    
    @patch('src.chain.business_value_chain.NovaLiteLLM')
    def test_llm_error_handling(self, mock_llm_class):
        """LLM 오류 처리 테스트"""
        # LLM이 예외를 발생시키도록 설정
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("LLM 호출 실패")
        mock_llm_class.return_value = mock_llm
        
        chain = BusinessValueChain()
        result = chain.invoke("테스트 프로젝트")
        
        # 오류 상황에서도 기본 구조 유지
        assert 'error' in result
        assert result['total_score'] == 0
        assert result['evaluation_type'] == 'error'
    
    def test_json_response_parsing(self):
        """JSON 응답 파싱 테스트"""
        json_response = '''
        {
            "pain_killer_score": 8.5,
            "vitamin_score": 7.0,
            "total_score": 7.9,
            "evaluation_type": "pain_killer_dominant",
            "reasoning": "테스트 평가 근거",
            "key_strengths": ["강점1", "강점2"],
            "improvement_areas": ["개선점1", "개선점2"]
        }
        '''
        
        result = self.chain._parse_evaluation_response(json_response)
        
        assert result['pain_killer_score'] == 8.5
        assert result['vitamin_score'] == 7.0
        assert result['total_score'] == 7.9
        assert result['evaluation_type'] == "pain_killer_dominant"
        assert len(result['key_strengths']) == 2
        assert len(result['improvement_areas']) == 2
    
    def test_invalid_json_fallback_parsing(self):
        """잘못된 JSON 응답 fallback 파싱 테스트"""
        invalid_response = "이것은 JSON이 아닙니다. 점수는 8점입니다."
        
        result = self.chain._parse_evaluation_response(invalid_response)
        
        # fallback 파싱 결과 검증
        assert 'total_score' in result
        assert 'evaluation_type' in result
        assert result['evaluation_type'] == 'fallback_parsed'
        assert 'reasoning' in result
    
    def test_score_validation(self):
        """점수 유효성 검증 테스트"""
        # 범위를 벗어난 점수가 포함된 JSON
        json_response = '''
        {
            "pain_killer_score": 15.0,
            "vitamin_score": -2.0,
            "total_score": 12.0,
            "evaluation_type": "test"
        }
        '''
        
        result = self.chain._parse_evaluation_response(json_response)
        
        # 점수가 0-10 범위로 조정되었는지 확인
        assert 0 <= result['pain_killer_score'] <= 10
        assert 0 <= result['vitamin_score'] <= 10
        assert 0 <= result['total_score'] <= 10
    
    def test_system_prompt_building(self):
        """시스템 프롬프트 구성 테스트"""
        system_prompt = self.chain._build_system_prompt()
        
        assert "Pain Killer 기준" in system_prompt
        assert "Vitamin 기준" in system_prompt
        assert "JSON 형식" in system_prompt
        assert "pain_killer_score" in system_prompt
        assert "vitamin_score" in system_prompt
    
    def test_user_prompt_building(self):
        """사용자 프롬프트 구성 테스트"""
        project_info = "테스트 프로젝트 정보"
        user_prompt = self.chain._build_user_prompt(project_info)
        
        assert project_info in user_prompt
        assert "비즈니스 가치를 평가해주세요" in user_prompt
        assert "JSON 형식으로만 응답해주세요" in user_prompt
    
    def test_run_method(self):
        """run 메서드 테스트"""
        score = self.chain.run()
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 10
    
    def test_multiple_invocations_consistency(self):
        """여러 번 호출 시 일관성 테스트"""
        test_input = "동일한 테스트 프로젝트"
        
        results = []
        for _ in range(3):
            result = self.chain.invoke(test_input)
            results.append(result['total_score'])
        
        # 점수 편차가 너무 크지 않은지 확인 (3점 이내)
        score_range = max(results) - min(results)
        assert score_range <= 3.0
    
    def test_different_evaluation_types(self):
        """다양한 평가 유형 테스트"""
        # Pain Killer 중심 프로젝트
        pain_killer_project = """
        응급실 대기시간 단축 시스템
        - 생명과 직결된 응급 상황 해결
        - 의료진 업무 효율성 극대화
        - 환자 안전성 향상
        """
        
        # Vitamin 중심 프로젝트  
        vitamin_project = """
        소셜 미디어 사진 필터 앱
        - 재미있는 사진 편집 기능
        - 소셜 공유 기능
        - 사용자 경험 향상
        """
        
        pain_result = self.chain.invoke(pain_killer_project)
        vitamin_result = self.chain.invoke(vitamin_project)
        
        # Pain Killer 프로젝트가 더 높은 Pain Killer 점수를 가져야 함
        assert pain_result['pain_killer_score'] >= vitamin_result['pain_killer_score']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])