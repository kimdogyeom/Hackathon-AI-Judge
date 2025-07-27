# -*- coding: utf-8 -*-
from langchain_core.runnables import RunnableParallel

from src.analysis import (
    VideoAnalysis,
    DocumentAnalysis,
    PresentationAnalysis
)
from src.chain import (
    AccessibilityChain,
    BusinessValueChain,
    CostAnalysisChain,
    InnovationChain,
    NetworkEffectChain,
    SocialImpactChain,
    SustainabilityChain,
    TechnicalFeasibilityChain,
    UserEngagementChain,
)
from src.classifier import ProjectTypeClassifier
from src.config.weight_manager import WeightManager


def main():
    """
    메인 실행 함수.
    """
    # 유저 데이터 입력(유저 업로드)
    # user_upload_chain = RunnableParallel({
    #   문서 업로드(TEXT)
    #   영상 업로드(VIDEO)
    #   발표자료 업로드(PDF,PNG...)
    # })
    # user_input = user_upload_chain.invoke()

    # 이곳에 문서의 예시 링크를 넣어주세요
    video_uri = ""
    document_uri = ""
    presentation_uri = ""

    # 입력된 데이터 프로세싱(분석)
    user_input = {
        "video_uri": video_uri,
        "document_uri": document_uri,
        "presentation_uri": presentation_uri
    }
    
    # 분석 클래스 인스턴스 생성
    video_analysis = VideoAnalysis()
    presentation_analysis = PresentationAnalysis()
    document_analysis = DocumentAnalysis()

    # 각 분석기에 해당하는 URI를 전달하는 입력 구성
    input_analysis_chain = RunnableParallel({
        "video_analysis": video_analysis,
        "presentation_analysis": presentation_analysis,
        "document_analysis": document_analysis
    })

    # 각 분석기에 s3_uri를 포함한 딕셔너리 전달
    analysis_input = {
        "video_analysis": {"s3_uri": user_input["video_uri"]},
        "document_analysis": {"s3_uri": user_input["document_uri"]},
        "presentation_analysis": {"s3_uri": user_input["presentation_uri"]}
    }

    evaluator_chain_input = input_analysis_chain.invoke(analysis_input)

    # 프로젝트 유형 분류기 실행
    classifier = ProjectTypeClassifier()
    type_result = classifier.classify(evaluator_chain_input)
    
    print(f"\n=== 프로젝트 유형 분류 결과 ===")
    print(f"프로젝트 유형: {type_result['project_type']}")
    print(f"신뢰도: {type_result['confidence']:.3f}")
    print(f"PainKiller 점수: {type_result['painkiller_score']:.3f}")
    print(f"Vitamin 점수: {type_result['vitamin_score']:.3f}")
    print(f"분류 근거: {type_result['reasoning']}")
    if type_result['warning_message']:
        print(f"경고: {type_result['warning_message']}")
    print()
    
    # 분석 결과를 평가 체인 입력 형태로 변환
    video_analysis_result = evaluator_chain_input.get("video_analysis", {})
    document_analysis_result = evaluator_chain_input.get("document_analysis", {})
    presentation_analysis_result = evaluator_chain_input.get("presentation_analysis", {})

    evaluator_chain_input = {
        "project_type": type_result,
        "video_analysis": video_analysis_result,
        "document_analysis": document_analysis_result,
        "presentation_analysis": presentation_analysis_result
    }

    # 모든 평가 체인 인스턴스 생성 (새로운 베이스 클래스 기반)
    evaluation_chains = {
        "business_value": BusinessValueChain(),
        "accessibility": AccessibilityChain(),
        "innovation": InnovationChain(),
        "cost_analysis": CostAnalysisChain(),
        "network_effect": NetworkEffectChain(),
        "social_impact": SocialImpactChain(),
        "sustainability": SustainabilityChain(),
        "technical_feasibility": TechnicalFeasibilityChain(),
        "user_engagement": UserEngagementChain(),
    }
    
    # 모든 평가 체인 실행
    results = {}
    for chain_name, chain in evaluation_chains.items():
        try:
            result = chain.invoke(evaluator_chain_input)
            results[chain_name] = result
        except Exception as e:
            print(f"경고: {chain_name} 평가 중 오류 발생: {e}")
            # 오류 발생 시 기본값 사용
            results[chain_name] = {
                "score": 0.0,
                "reasoning": f"평가 중 오류 발생: {str(e)}",
                "suggestions": ["시스템 관리자에게 문의하세요"],
                "execution_time": 0.0,
                "error": str(e)
            }

    # WeightManager를 사용하여 가중치 적용
    weight_manager = WeightManager()
    project_type = type_result['project_type']
    
    # 가중치 정보 출력
    print(f"\n=== 가중치 정보 ===")
    print(weight_manager.get_weight_summary(project_type))
    print(f"\n==================")
    
    # 결과 출력 및 점수 추출
    print("\n=== 평가 결과 ===\n")
    scores = {}
    
    for category, result in results.items():
        if isinstance(result, dict):
            # 표준화된 결과에서 점수 추출
            if category == "business_value" and "total_score" in result:
                # BusinessValueChain의 특별한 경우
                score = result.get("total_score", 0)
            else:
                score = result.get("score", 0)
            
            print(f"{category}: {score:.2f}/10")
            
            # 추가 정보 출력
            if result.get("execution_time"):
                print(f"  - 실행 시간: {result['execution_time']:.3f}초")
            
            if result.get("reasoning"):
                reasoning = result["reasoning"][:100] + "..." if len(result["reasoning"]) > 100 else result["reasoning"]
                print(f"  - 평가 근거: {reasoning}")
            
            if result.get("suggestions") and len(result["suggestions"]) > 0:
                print(f"  - 주요 개선사항: {result['suggestions'][0][:60]}...")
            
            if result.get("data_limitations"):
                print(f"  - 데이터 제한: {result['data_limitations'][:60]}...")
            
            if result.get("error"):
                print(f"  - 오류: {result['error'][:60]}...")
            
            print()  # 빈 줄 추가
            
        else:
            # 레거시 결과 형식 처리
            score = float(result) if result else 0.0
            print(f"{category}: {score:.2f}/10\n")
        
        scores[category] = score
    
    # 가중치를 적용한 최종 점수 계산
    final_score = weight_manager.calculate_final_score(scores, project_type)
    
    # 가중치 적용 세부사항 출력
    weights = weight_manager.get_weights(project_type)
    weighted_scores = weight_manager.apply_weights(scores, weights)
    
    print("=== 가중치 적용 세부사항 ===")
    for chain_name in sorted(weighted_scores.keys(), key=lambda x: weighted_scores[x], reverse=True):
        original_score = scores[chain_name]
        weight = weights[chain_name]
        weighted_score = weighted_scores[chain_name]
        print(f"{chain_name}: {original_score:.2f} × {weight:.3f} = {weighted_score:.3f}")
    
    print(f"\n최종 가중 점수: {final_score:.2f}/10")
    print(f"프로젝트 유형: {project_type.upper()}")


if __name__ == "__main__":
    main()
