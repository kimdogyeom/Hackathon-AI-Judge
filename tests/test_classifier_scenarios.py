#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
프로젝트 유형 분류기 시나리오 테스트
"""

from src.classifier import ProjectTypeClassifier

def test_painkiller_scenario():
    """PainKiller 시나리오 테스트"""
    classifier = ProjectTypeClassifier()
    
    test_data = {
        "document_analysis": {
            "content": """
            이 프로젝트는 중소기업의 재고 관리 문제를 해결하는 AI 기반 솔루션입니다.
            기존 수작업으로 인한 오류를 90% 감소시키고, 재고 관리 비용을 30% 절감합니다.
            자동화된 프로세스로 업무 효율성을 크게 개선하여 생산성을 향상시킵니다.
            """
        },
        "presentation_analysis": {
            "summary": "비용 절감과 효율성 개선을 통한 문제 해결형 솔루션"
        }
    }
    
    result = classifier.classify(test_data)
    print("=== PainKiller 시나리오 ===")
    print(f"프로젝트 유형: {result['project_type']}")
    print(f"신뢰도: {result['confidence']:.3f}")
    print(f"PainKiller 점수: {result['painkiller_score']:.3f}")
    print(f"Vitamin 점수: {result['vitamin_score']:.3f}")
    print(f"분류 근거: {result['reasoning']}")
    if result['warning_message']:
        print(f"경고: {result['warning_message']}")
    print()

def test_vitamin_scenario():
    """Vitamin 시나리오 테스트"""
    classifier = ProjectTypeClassifier()
    
    test_data = {
        "document_analysis": {
            "content": """
            이 앱은 사용자 경험을 혁신하는 소셜 플랫폼입니다.
            창의적인 콘텐츠 공유와 커뮤니티 참여를 통해 즐거움을 제공합니다.
            개인화된 추천 시스템으로 사용자 만족도를 높이고 참여도를 증진시킵니다.
            """
        },
        "presentation_analysis": {
            "summary": "혁신적인 사용자 경험과 소셜 기능을 통한 엔터테인먼트 서비스"
        }
    }
    
    result = classifier.classify(test_data)
    print("=== Vitamin 시나리오 ===")
    print(f"프로젝트 유형: {result['project_type']}")
    print(f"신뢰도: {result['confidence']:.3f}")
    print(f"PainKiller 점수: {result['painkiller_score']:.3f}")
    print(f"Vitamin 점수: {result['vitamin_score']:.3f}")
    print(f"분류 근거: {result['reasoning']}")
    if result['warning_message']:
        print(f"경고: {result['warning_message']}")
    print()

def test_balanced_scenario():
    """Balanced 시나리오 테스트"""
    classifier = ProjectTypeClassifier()
    
    test_data = {
        "document_analysis": {
            "content": """
            이 플랫폼은 일반적인 비즈니스 솔루션입니다.
            다양한 기능을 제공하여 사용자들에게 도움을 줍니다.
            """
        }
    }
    
    result = classifier.classify(test_data)
    print("=== Balanced 시나리오 ===")
    print(f"프로젝트 유형: {result['project_type']}")
    print(f"신뢰도: {result['confidence']:.3f}")
    print(f"PainKiller 점수: {result['painkiller_score']:.3f}")
    print(f"Vitamin 점수: {result['vitamin_score']:.3f}")
    print(f"분류 근거: {result['reasoning']}")
    if result['warning_message']:
        print(f"경고: {result['warning_message']}")
    print()

def test_mixed_scenario():
    """혼합 키워드 시나리오 테스트"""
    classifier = ProjectTypeClassifier()
    
    test_data = {
        "document_analysis": {
            "content": """
            이 프로젝트는 비용 절감과 효율성 개선을 통해 문제를 해결하면서도,
            동시에 사용자 경험을 혁신하고 창의적인 기능을 제공합니다.
            자동화로 생산성을 향상시키고, 소셜 기능으로 사용자 참여도를 높입니다.
            """
        }
    }
    
    result = classifier.classify(test_data)
    print("=== 혼합 키워드 시나리오 ===")
    print(f"프로젝트 유형: {result['project_type']}")
    print(f"신뢰도: {result['confidence']:.3f}")
    print(f"PainKiller 점수: {result['painkiller_score']:.3f}")
    print(f"Vitamin 점수: {result['vitamin_score']:.3f}")
    print(f"분류 근거: {result['reasoning']}")
    if result['warning_message']:
        print(f"경고: {result['warning_message']}")
    print()

def test_classification_info():
    """분류기 설정 정보 테스트"""
    classifier = ProjectTypeClassifier()
    info = classifier.get_classification_info()
    
    print("=== 분류기 설정 정보 ===")
    print(f"신뢰도 임계값: {info['confidence_threshold']}")
    print(f"PainKiller 키워드 수: {info['painkiller_keywords_count']}")
    print(f"Vitamin 키워드 수: {info['vitamin_keywords_count']}")
    print(f"PainKiller 키워드 예시: {info['painkiller_keywords']}")
    print(f"Vitamin 키워드 예시: {info['vitamin_keywords']}")
    print()

if __name__ == "__main__":
    print("프로젝트 유형 분류기 시나리오 테스트 시작\n")
    
    test_painkiller_scenario()
    test_vitamin_scenario()
    test_balanced_scenario()
    test_mixed_scenario()
    test_classification_info()
    
    print("모든 시나리오 테스트 완료!")