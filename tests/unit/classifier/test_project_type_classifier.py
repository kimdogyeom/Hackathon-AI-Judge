# -*- coding: utf-8 -*-
"""
프로젝트 유형 분류기 단위 테스트
"""
import pytest
import tempfile
import yaml
from pathlib import Path
from src.classifier import ProjectTypeClassifier


class TestProjectTypeClassifier:
    """프로젝트 유형 분류기 테스트 클래스"""
    
    @pytest.fixture
    def classifier(self):
        """기본 분류기 인스턴스"""
        return ProjectTypeClassifier()
    
    @pytest.fixture
    def custom_config_classifier(self):
        """커스텀 설정을 사용하는 분류기 인스턴스"""
        # 임시 설정 파일 생성
        config_data = {
            "classification": {
                "confidence_threshold": 0.8,
                "painkiller_keywords": ["효율성", "비용절감", "자동화"],
                "vitamin_keywords": ["재미", "경험", "혁신"]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f, allow_unicode=True)
            temp_path = f.name
        
        classifier = ProjectTypeClassifier(config_path=temp_path)
        
        # 테스트 후 임시 파일 정리
        yield classifier
        Path(temp_path).unlink()
    
    def test_painkiller_classification(self, classifier):
        """PainKiller 유형 분류 테스트"""
        test_data = {
            "document_analysis": {
                "content": "이 솔루션은 비용 절감과 효율성 개선을 통해 생산성을 향상시킵니다. 자동화로 업무 프로세스를 개선합니다."
            },
            "presentation_analysis": {
                "summary": "문제 해결 중심의 접근으로 시간 단축을 실현합니다."
            }
        }
        
        result = classifier.classify(test_data)
        
        assert result["project_type"] == "painkiller"
        assert result["confidence"] >= 0.7
        assert result["painkiller_score"] > result["vitamin_score"]
        assert result["warning_message"] is None
        assert "문제 해결형" in result["reasoning"]
    
    def test_vitamin_classification(self, classifier):
        """Vitamin 유형 분류 테스트"""
        test_data = {
            "document_analysis": {
                "content": "사용자 경험을 혁신하고 창의성을 발휘하여 즐거운 서비스를 제공합니다."
            },
            "presentation_analysis": {
                "summary": "소셜 커뮤니티 기능으로 사용자 참여도와 만족도를 높입니다."
            }
        }
        
        result = classifier.classify(test_data)
        
        assert result["project_type"] == "vitamin"
        assert result["confidence"] >= 0.7
        assert result["vitamin_score"] > result["painkiller_score"]
        assert result["warning_message"] is None
        assert "개선형" in result["reasoning"]
    
    def test_balanced_classification_low_confidence(self, classifier):
        """신뢰도 낮은 경우 Balanced 분류 테스트"""
        test_data = {
            "document_analysis": {
                "content": "일반적인 비즈니스 솔루션입니다."
            }
        }
        
        result = classifier.classify(test_data)
        
        assert result["project_type"] == "balanced"
        assert result["confidence"] < 0.7
        assert result["painkiller_score"] == 0.5
        assert result["vitamin_score"] == 0.5
        assert result["warning_message"] is not None
        assert "복합형" in result["reasoning"]
    
    def test_mixed_keywords_classification(self, classifier):
        """혼합 키워드가 있는 경우 테스트"""
        test_data = {
            "document_analysis": {
                "content": "비용 절감을 통한 효율성 개선과 동시에 사용자 경험 혁신을 추구합니다."
            }
        }
        
        result = classifier.classify(test_data)
        
        # 결과는 painkiller, vitamin, balanced 중 하나여야 함
        assert result["project_type"] in ["painkiller", "vitamin", "balanced"]
        assert 0.0 <= result["confidence"] <= 1.0
        assert 0.0 <= result["painkiller_score"] <= 1.0
        assert 0.0 <= result["vitamin_score"] <= 1.0
        assert abs(result["painkiller_score"] + result["vitamin_score"] - 1.0) < 0.001  # 합이 1에 가까워야 함
    
    def test_empty_data_handling(self, classifier):
        """빈 데이터 처리 테스트"""
        test_data = {}
        
        result = classifier.classify(test_data)
        
        assert result["project_type"] == "balanced"
        assert result["confidence"] == 0.0
        assert result["painkiller_score"] == 0.5
        assert result["vitamin_score"] == 0.5
        assert result["warning_message"] is not None
    
    def test_custom_config(self, custom_config_classifier):
        """커스텀 설정 테스트"""
        info = custom_config_classifier.get_classification_info()
        
        assert info["confidence_threshold"] == 0.8
        assert info["painkiller_keywords_count"] == 3
        assert info["vitamin_keywords_count"] == 3
    
    def test_keyword_score_calculation(self, classifier):
        """키워드 점수 계산 테스트"""
        # private 메서드 테스트를 위해 직접 호출
        text = "이 프로젝트는 비용 절감과 효율성 개선을 목표로 합니다."
        painkiller_keywords = ["비용 절감", "효율성 개선"]
        
        score = classifier._calculate_keyword_score(text, painkiller_keywords)
        
        assert score > 0
        assert isinstance(score, float)
    
    def test_text_extraction(self, classifier):
        """텍스트 추출 테스트"""
        test_data = {
            "document_analysis": {
                "content": "문서 내용",
                "summary": "문서 요약"
            },
            "video_analysis": {
                "text": "비디오 텍스트"
            },
            "presentation_analysis": "발표 내용"
        }
        
        extracted_text = classifier._extract_text_from_analysis(test_data)
        
        assert "문서 내용" in extracted_text
        assert "문서 요약" in extracted_text
        assert "비디오 텍스트" in extracted_text
        assert "발표 내용" in extracted_text
    
    def test_error_handling(self, classifier):
        """오류 처리 테스트"""
        # 잘못된 데이터 타입 전달
        invalid_data = "invalid_string_data"
        
        result = classifier.classify(invalid_data)
        
        assert result["project_type"] == "balanced"
        assert result["confidence"] == 0.0
        assert result["warning_message"] is not None
        assert "오류" in result["warning_message"]
    
    def test_confidence_threshold_boundary(self, classifier):
        """신뢰도 임계값 경계 테스트"""
        # 임계값 정확히 0.7인 경우를 시뮬레이션하기 위해
        # 특정 키워드 조합 사용
        test_data = {
            "document_analysis": {
                "content": "효율성 개선 비용 절감 자동화"  # PainKiller 키워드만
            }
        }
        
        result = classifier.classify(test_data)
        
        # 한쪽 키워드만 있으므로 신뢰도가 높아야 함
        assert result["confidence"] >= 0.7
        assert result["project_type"] == "painkiller"
    
    def test_classification_info(self, classifier):
        """분류 정보 반환 테스트"""
        info = classifier.get_classification_info()
        
        assert "confidence_threshold" in info
        assert "painkiller_keywords_count" in info
        assert "vitamin_keywords_count" in info
        assert "painkiller_keywords" in info
        assert "vitamin_keywords" in info
        
        assert info["confidence_threshold"] == 0.7
        assert info["painkiller_keywords_count"] > 0
        assert info["vitamin_keywords_count"] > 0
        assert len(info["painkiller_keywords"]) <= 5
        assert len(info["vitamin_keywords"]) <= 5