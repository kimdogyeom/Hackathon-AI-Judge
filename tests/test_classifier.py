# -*- coding: utf-8 -*-
"""
프로젝트 유형 분류기 테스트 스크립트
"""
from src.classifier import ProjectTypeClassifier

def test_classifier():
    """분류기 기본 동작 테스트"""
    classifier = ProjectTypeClassifier()
    
    # 테스트 데이터 1: PainKiller 유형
    painkiller_data = {
        "document_analysis": {
            "content": "이 프로젝트는 기업의 비용 절감과 효율성 개선을 목표로 합니다. 자동화를 통해 업무 프로세스를 개선하고 생산성을 향상시킵니다."
        },
        "presentation_analysis": {
            "summary": "문제 해결 중심의 솔루션으로 시간 단축과 오류 감소를 실현합니다."
        }
    }
    
    # 테스트 데이터 2: Vitamin 유형  
    vitamin_data = {
        "document_analysis": {
            "content": "사용자 경험을 혁신하고 창의성을 발휘하여 즐거운 서비스를 제공합니다. 소셜 커뮤니티 기능으로 사용자 참여도를 높입니다."
        },
        "presentation_analysis": {
            "summary": "개인화된 엔터테인먼트 경험으로 사용자 만족도를 극대화합니다."
        }
    }
    
    # 테스트 데이터 3: 혼합 유형
    mixed_data = {
        "document_analysis": {
            "content": "일반적인 비즈니스 솔루션입니다."
        }
    }
    
    print("=== 프로젝트 유형 분류기 테스트 ===\n")
    
    # 분류기 정보 출력
    info = classifier.get_classification_info()
    print(f"신뢰도 임계값: {info['confidence_threshold']}")
    print(f"PainKiller 키워드 수: {info['painkiller_keywords_count']}")
    print(f"Vitamin 키워드 수: {info['vitamin_keywords_count']}")
    print()
    
    # 테스트 실행
    test_cases = [
        ("PainKiller 테스트", painkiller_data),
        ("Vitamin 테스트", vitamin_data),
        ("혼합 유형 테스트", mixed_data)
    ]
    
    for test_name, test_data in test_cases:
        print(f"--- {test_name} ---")
        result = classifier.classify(test_data)
        
        print(f"프로젝트 유형: {result['project_type']}")
        print(f"신뢰도: {result['confidence']:.3f}")
        print(f"PainKiller 점수: {result['painkiller_score']:.3f}")
        print(f"Vitamin 점수: {result['vitamin_score']:.3f}")
        print(f"분류 근거: {result['reasoning']}")
        if result['warning_message']:
            print(f"경고: {result['warning_message']}")
        print()

if __name__ == "__main__":
    test_classifier()