#!/usr/bin/env python3
"""
가중치 관리자 통합 테스트

실제 설정 파일을 사용하여 WeightManager의 동작을 확인합니다.
"""

from src.config.weight_manager import WeightManager, ProjectType


def test_weight_manager_integration():
    """WeightManager 통합 테스트"""
    print("=== 가중치 관리자 통합 테스트 ===\n")
    
    # WeightManager 초기화
    manager = WeightManager()
    
    # 사용 가능한 프로젝트 유형 확인
    project_types = manager.get_available_project_types()
    print(f"사용 가능한 프로젝트 유형: {project_types}\n")
    
    # 각 프로젝트 유형별 가중치 확인
    for project_type in project_types:
        print(f"=== {project_type.upper()} 유형 가중치 ===")
        weights = manager.get_weights(project_type)
        
        # 가중치 합계 확인
        total_weight = sum(weights.values())
        print(f"가중치 합계: {total_weight:.3f}")
        
        # 상위 3개 가중치 출력
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        print("상위 3개 가중치:")
        for i, (chain, weight) in enumerate(sorted_weights[:3]):
            print(f"  {i+1}. {chain}: {weight:.3f} ({weight*100:.1f}%)")
        print()
    
    # 가중치 적용 테스트
    print("=== 가중치 적용 테스트 ===")
    sample_scores = {
        'business_value': 8.5,
        'technical_feasibility': 7.2,
        'cost_analysis': 6.8,
        'user_engagement': 9.1,
        'innovation': 8.0,
        'social_impact': 7.5,
        'sustainability': 6.5,
        'accessibility': 7.8,
        'network_effect': 6.2
    }
    
    print("원본 점수:")
    for chain, score in sample_scores.items():
        print(f"  {chain}: {score}")
    print()
    
    # 각 프로젝트 유형별 최종 점수 계산
    for project_type in project_types:
        final_score = manager.calculate_final_score(sample_scores, project_type)
        print(f"{project_type} 유형 최종 점수: {final_score:.2f}")
    
    print("\n=== 가중치 요약 정보 ===")
    summary = manager.get_weight_summary('painkiller')
    print(summary)
    
    print("\n✅ 통합 테스트 완료!")


if __name__ == "__main__":
    test_weight_manager_integration()