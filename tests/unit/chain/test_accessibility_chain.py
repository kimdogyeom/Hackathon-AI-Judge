# -*- coding: utf-8 -*-
"""
AccessibilityChain 테스트
"""

import pytest
import logging
from src.chain.accessibility_chain import AccessibilityChain

# 로거 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class TestAccessibilityChain:
    """AccessibilityChain 테스트 클래스"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.chain = AccessibilityChain()
    
    def test_initialization(self):
        """AccessibilityChain 초기화 테스트"""
        assert self.chain.chain_name == "AccessibilityChain"
        assert hasattr(self.chain, 'accessibility_keywords')
        assert hasattr(self.chain, 'negative_keywords')
        
        # WCAG 4가지 원칙 키워드 확인
        assert 'perceivable' in self.chain.accessibility_keywords
        assert 'operable' in self.chain.accessibility_keywords
        assert 'understandable' in self.chain.accessibility_keywords
        assert 'robust' in self.chain.accessibility_keywords
    
    def test_high_accessibility_content(self):
        """접근성이 잘 고려된 콘텐츠 테스트"""
        high_accessibility_data = {
            'document_analysis': {
                'content': '''
                이 프로젝트는 WCAG 2.1 가이드라인을 준수하여 개발되었습니다.
                시각 장애인을 위한 스크린 리더 지원과 모든 이미지에 대체 텍스트를 제공합니다.
                키보드 네비게이션이 완벽하게 지원되며, 색상 대비비는 4.5:1 이상을 유지합니다.
                명확한 사용자 가이드와 도움말 시스템을 제공하며, 다양한 브라우저에서 테스트되었습니다.
                '''
            },
            'video_analysis': {
                'content': '''
                비디오에는 자막과 수화 통역이 제공되며, 보조 기술과의 호환성을 고려했습니다.
                웹 표준을 준수하고 HTML 유효성 검증을 통과했습니다.
                '''
            }
        }
        
        result = self.chain.invoke(high_accessibility_data)
        
        # 기본 구조 검증
        assert isinstance(result, dict)
        assert 'score' in result
        assert 'reasoning' in result
        assert 'suggestions' in result
        assert 'execution_time' in result
        assert 'detailed_scores' in result
        
        # 점수 범위 검증
        assert 0.0 <= result['score'] <= 10.0
        
        # 높은 접근성 점수 기대
        assert result['score'] >= 6.0, f"높은 접근성 콘텐츠의 점수가 낮음: {result['score']}"
        
        # 상세 점수 확인
        detailed = result['detailed_scores']
        assert detailed['perceivable'] >= 5.0  # 인식 가능성 높음
        assert detailed['operable'] >= 3.0     # 운용 가능성 높음
        
        logger.info(f"고접근성 콘텐츠 점수: {result['score']:.2f}")
    
    def test_low_accessibility_content(self):
        """접근성이 부족한 콘텐츠 테스트"""
        low_accessibility_data = {
            'document_analysis': {
                'content': '''
                이 프로젝트는 시각적으로만 디자인되었습니다.
                마우스 필수 사용이며 복잡한 인터페이스를 가지고 있습니다.
                작은 글씨와 낮은 색상 대비를 사용합니다.
                '''
            }
        }
        
        result = self.chain.invoke(low_accessibility_data)
        
        # 기본 구조 검증
        assert isinstance(result, dict)
        assert 'score' in result
        assert 'reasoning' in result
        assert 'suggestions' in result
        
        # 낮은 점수 기대
        assert result['score'] <= 3.0, f"낮은 접근성 콘텐츠의 점수가 높음: {result['score']}"
        
        # 개선 제안이 많아야 함
        assert len(result['suggestions']) >= 3
        
        logger.info(f"저접근성 콘텐츠 점수: {result['score']:.2f}")
    
    def test_mixed_accessibility_content(self):
        """일부 접근성 요소만 있는 콘텐츠 테스트"""
        mixed_data = {
            'document_analysis': {
                'content': '''
                이 프로젝트는 키보드 네비게이션을 지원하고 명확한 사용자 가이드를 제공합니다.
                하지만 색상 대비나 대체 텍스트에 대한 고려는 부족합니다.
                '''
            },
            'presentation_analysis': {
                'content': '일부 접근성 기능은 구현되어 있으나 완전하지 않습니다.'
            }
        }
        
        result = self.chain.invoke(mixed_data)
        
        # 중간 정도의 점수 기대
        assert 2.0 <= result['score'] <= 6.0, f"혼합 접근성 콘텐츠의 점수가 범위를 벗어남: {result['score']}"
        
        # 상세 점수에서 일부는 높고 일부는 낮아야 함
        detailed = result['detailed_scores']
        scores = list(detailed.values())
        assert max(scores) > min(scores), "상세 점수들이 모두 비슷함"
        
        logger.info(f"혼합 접근성 콘텐츠 점수: {result['score']:.2f}")
    
    def test_empty_data(self):
        """빈 데이터 처리 테스트"""
        empty_data = {}
        result = self.chain.invoke(empty_data)
        
        # 기본 구조는 유지되어야 함
        assert isinstance(result, dict)
        assert 'score' in result
        assert 'reasoning' in result
        assert 'suggestions' in result
        
        # 데이터 제한사항 표시
        assert 'data_limitations' in result
        assert len(result['data_limitations']) > 0
        
        # 낮은 점수 (데이터 부족)
        assert result['score'] <= 1.0
        
        logger.info(f"빈 데이터 점수: {result['score']:.2f}")
    
    def test_wcag_principles_evaluation(self):
        """WCAG 4가지 원칙별 평가 테스트"""
        # 각 원칙별로 특화된 콘텐츠 테스트
        test_cases = [
            {
                'name': 'perceivable',
                'content': '대체 텍스트, 스크린 리더, 색상 대비, 자막을 제공합니다.',
                'expected_high': 'perceivable'
            },
            {
                'name': 'operable', 
                'content': '키보드 네비게이션, 포커스, 탭 순서, 접근 키를 지원합니다.',
                'expected_high': 'operable'
            },
            {
                'name': 'understandable',
                'content': '명확한 언어, 간단한 설명, 사용자 가이드, 도움말을 제공합니다.',
                'expected_high': 'understandable'
            },
            {
                'name': 'robust',
                'content': '호환성, 다양한 브라우저, 보조 기술, 웹 표준을 지원합니다.',
                'expected_high': 'robust'
            }
        ]
        
        for test_case in test_cases:
            data = {
                'document_analysis': {
                    'content': test_case['content']
                }
            }
            
            result = self.chain.invoke(data)
            detailed = result['detailed_scores']
            
            # 해당 원칙의 점수가 다른 원칙보다 높아야 함
            expected_principle = test_case['expected_high']
            expected_score = detailed[expected_principle]
            
            other_scores = [score for key, score in detailed.items() if key != expected_principle]
            max_other_score = max(other_scores) if other_scores else 0
            
            assert expected_score >= max_other_score, \
                f"{expected_principle} 원칙 점수가 예상보다 낮음: {expected_score} vs {max_other_score}"
            
            logger.info(f"{test_case['name']} 테스트 - {expected_principle}: {expected_score:.2f}")
    
    def test_negative_keywords_impact(self):
        """부정적 키워드의 영향 테스트"""
        negative_data = {
            'document_analysis': {
                'content': '''
                이 프로젝트는 접근성 고려 안함, 시각적으로만 디자인,
                마우스 필수, 복잡한 인터페이스, 작은 글씨를 사용합니다.
                '''
            }
        }
        
        positive_data = {
            'document_analysis': {
                'content': '''
                이 프로젝트는 접근성을 고려하여 설계되었습니다.
                키보드 네비게이션과 명확한 인터페이스를 제공합니다.
                '''
            }
        }
        
        negative_result = self.chain.invoke(negative_data)
        positive_result = self.chain.invoke(positive_data)
        
        # 부정적 키워드가 있는 경우 점수가 더 낮아야 함
        assert negative_result['score'] < positive_result['score'], \
            f"부정적 키워드의 영향이 반영되지 않음: {negative_result['score']} >= {positive_result['score']}"
        
        logger.info(f"부정적 키워드 영향 - 부정: {negative_result['score']:.2f}, 긍정: {positive_result['score']:.2f}")
    
    def test_base_class_interface_compliance(self):
        """베이스 클래스 인터페이스 준수 테스트"""
        # EvaluationChainBase의 표준 인터페이스 확인
        assert hasattr(self.chain, 'invoke')
        assert hasattr(self.chain, '_analyze')
        assert hasattr(self.chain, 'chain_name')
        assert hasattr(self.chain, 'logger')
        
        # invoke 메서드 호출 가능
        result = self.chain.invoke({})
        
        # 표준 출력 형식 확인
        required_fields = ['score', 'reasoning', 'suggestions', 'execution_time', 'chain_name']
        for field in required_fields:
            assert field in result, f"필수 필드 {field}가 결과에 없음"
        
        # 타입 검증
        assert isinstance(result['score'], (int, float))
        assert isinstance(result['reasoning'], str)
        assert isinstance(result['suggestions'], list)
        assert isinstance(result['execution_time'], (int, float))
        assert isinstance(result['chain_name'], str)
        
        assert result['chain_name'] == 'AccessibilityChain'
    
    def test_error_handling(self):
        """오류 처리 테스트"""
        # 잘못된 형식의 데이터
        invalid_data_types = [
            "string_input",
            123,
            None,
            []
        ]
        
        for invalid_data in invalid_data_types:
            try:
                result = self.chain.invoke(invalid_data)
                # 오류가 발생하지 않았다면 적절한 기본값을 반환해야 함
                assert isinstance(result, dict)
                assert 'score' in result
                assert result['score'] >= 0.0
            except Exception as e:
                # 예외가 발생해도 적절히 처리되어야 함
                logger.info(f"예상된 예외 발생: {e}")
    
    def test_suggestions_quality(self):
        """개선 제안의 품질 테스트"""
        test_data = {
            'document_analysis': {
                'content': '기본적인 웹 애플리케이션입니다.'
            }
        }
        
        result = self.chain.invoke(test_data)
        suggestions = result['suggestions']
        
        # 제안이 있어야 함
        assert len(suggestions) > 0
        
        # 각 제안이 의미있는 문자열이어야 함
        for suggestion in suggestions:
            assert isinstance(suggestion, str)
            assert len(suggestion.strip()) > 10  # 최소한의 길이
            assert not suggestion.strip().startswith('TODO')  # TODO가 아닌 실제 제안
        
        # 중복 제안이 없어야 함
        assert len(suggestions) == len(set(suggestions))
        
        logger.info(f"제안 개수: {len(suggestions)}")
        for i, suggestion in enumerate(suggestions, 1):
            logger.info(f"  {i}. {suggestion}")
    
    def test_execution_time_logging(self):
        """실행 시간 로깅 테스트"""
        test_data = {
            'document_analysis': {
                'content': '테스트 콘텐츠입니다.'
            }
        }
        
        result = self.chain.invoke(test_data)
        
        # 실행 시간이 기록되어야 함
        assert 'execution_time' in result
        assert isinstance(result['execution_time'], (int, float))
        assert result['execution_time'] >= 0
        
        # 일반적으로 1초 이내에 완료되어야 함
        assert result['execution_time'] < 1.0
        
        logger.info(f"실행 시간: {result['execution_time']:.3f}초")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])