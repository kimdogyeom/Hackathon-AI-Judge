# -*- coding: utf-8 -*-
"""
InnovationChain 통합 테스트
main.py와의 통합을 확인합니다.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.chain.innovation_chain import InnovationChain


def test_innovation_chain_integration():
    """InnovationChain 통합 테스트"""
    print("=== InnovationChain 통합 테스트 시작 ===")
    
    # InnovationChain 인스턴스 생성 (LLM 자동 초기화)
    innovation_chain = InnovationChain()
    
    # 테스트 데이터 준비
    test_data = {
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
    
    try:
        # invoke 메서드 테스트
        print("1. invoke 메서드 테스트...")
        result = innovation_chain.invoke(test_data)
        
        print(f"   - 점수: {result.get('score', 'N/A')}")
        print(f"   - 실행 시간: {result.get('execution_time', 'N/A')}초")
        print(f"   - 체인 이름: {result.get('chain_name', 'N/A')}")
        print(f"   - 평가 근거: {result.get('reasoning', 'N/A')[:100]}...")
        print(f"   - 개선 제안 수: {len(result.get('suggestions', []))}")
        
        # __call__ 메서드 테스트 (기존 호환성)
        print("\n2. __call__ 메서드 테스트...")
        call_result = innovation_chain(test_data)
        print(f"   - 점수: {call_result.get('score', 'N/A')}")
        
        # run 메서드 테스트 (기존 호환성)
        print("\n3. run 메서드 테스트...")
        run_score = innovation_chain.run()
        print(f"   - 점수: {run_score}")
        
        print("\n=== 모든 테스트 성공! ===")
        return True
        
    except Exception as e:
        print(f"\n=== 테스트 실패: {str(e)} ===")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_innovation_chain_integration()
    sys.exit(0 if success else 1)