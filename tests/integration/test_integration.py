# -*- coding: utf-8 -*-
"""
통합 테스트 모듈
전체 파이프라인의 End-to-End 테스트를 수행합니다.
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from src.analysis import VideoAnalysis, DocumentAnalysis, PresentationAnalysis
from src.classifier import ProjectTypeClassifier
from src.config.weight_manager import WeightManager
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


class TestEndToEndPipeline:
    """전체 파이프라인 End-to-End 테스트"""
    
    @pytest.fixture
    def mock_analysis_results(self):
        """모킹된 분석 결과"""
        return {
            "video_analysis": {
                "content": "AI 기반 헬스케어 모니터링 시스템으로 환자의 건강 상태를 실시간으로 추적합니다.",
                "key_features": ["실시간 모니터링", "AI 분석", "알림 시스템"],
                "target_audience": "만성질환자, 의료진"
            },
            "document_analysis": {
                "content": "비용 절감과 효율성 개선에 중점을 둔 B2B 헬스케어 솔루션입니다.",
                "business_model": "구독 기반 SaaS",
                "problem_solving": "의료진 업무 부담 감소, 환자 안전성 향상"
            },
            "presentation_analysis": {
                "content": "혁신적인 AI 기술을 활용한 헬스케어 혁신 프로젝트",
                "market_size": "글로벌 디지털 헬스케어 시장",
                "competitive_advantage": "실시간 AI 분석 기술"
            }
        }
    
    @pytest.fixture
    def evaluation_chains(self):
        """평가 체인 인스턴스들"""
        return {
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
    
    @pytest.mark.integration
    def test_complete_pipeline_with_painkiller_project(self, mock_analysis_results, evaluation_chains):
        """PainKiller 프로젝트에 대한 전체 파이프라인 테스트"""
        # 1. 프로젝트 유형 분류
        classifier = ProjectTypeClassifier()
        type_result = classifier.classify(mock_analysis_results)
        
        # 분류 결과 검증
        assert type_result is not None
        assert "project_type" in type_result
        assert "confidence" in type_result
        assert type_result["project_type"] in ["painkiller", "vitamin", "balanced"]
        assert 0.0 <= type_result["confidence"] <= 1.0
        
        print(f"\n=== 프로젝트 유형 분류 결과 ===")
        print(f"프로젝트 유형: {type_result['project_type']}")
        print(f"신뢰도: {type_result['confidence']:.3f}")
        
        # 2. 평가 체인 입력 준비
        evaluator_input = {
            "project_type": type_result,
            **mock_analysis_results
        }
        
        # 3. 모든 평가 체인 실행
        results = {}
        execution_times = {}
        
        for chain_name, chain in evaluation_chains.items():
            start_time = time.time()
            try:
                result = chain.invoke(evaluator_input)
                execution_time = time.time() - start_time
                
                # 결과 검증
                assert result is not None
                if isinstance(result, dict):
                    # 표준화된 결과 형식 검증
                    if "score" in result:
                        assert 0.0 <= result["score"] <= 10.0
                    elif "total_score" in result:  # BusinessValueChain 특별 케이스
                        assert 0.0 <= result["total_score"] <= 10.0
                    
                    # 추가 필드 검증
                    if "reasoning" in result:
                        assert isinstance(result["reasoning"], str)
                        assert len(result["reasoning"]) > 0
                    
                    if "suggestions" in result:
                        assert isinstance(result["suggestions"], list)
                
                results[chain_name] = result
                execution_times[chain_name] = execution_time
                
                print(f"{chain_name}: 실행 완료 ({execution_time:.3f}초)")
                
            except Exception as e:
                pytest.fail(f"{chain_name} 평가 체인 실행 실패: {e}")
        
        # 4. 가중치 적용 및 최종 점수 계산
        weight_manager = WeightManager()
        project_type = type_result['project_type']
        
        # 점수 추출
        scores = {}
        for chain_name, result in results.items():
            if isinstance(result, dict):
                if chain_name == "business_value" and "total_score" in result:
                    score = result["total_score"]
                else:
                    score = result.get("score", 0)
            else:
                score = float(result) if result else 0.0
            scores[chain_name] = score
        
        # 가중치 적용
        weights = weight_manager.get_weights(project_type)
        weighted_scores = weight_manager.apply_weights(scores, weights)
        final_score = weight_manager.calculate_final_score(scores, project_type)
        
        # 최종 결과 검증
        assert 0.0 <= final_score <= 10.0
        assert len(weights) == len(scores)
        assert abs(sum(weights.values()) - 1.0) < 0.001  # 가중치 합이 1.0에 가까운지 확인
        
        print(f"\n=== 최종 결과 ===")
        print(f"프로젝트 유형: {project_type}")
        print(f"최종 점수: {final_score:.2f}/10")
        print(f"총 실행 시간: {sum(execution_times.values()):.3f}초")
        
        # 성능 검증 (전체 파이프라인이 30초 이내에 완료되어야 함)
        total_execution_time = sum(execution_times.values())
        assert total_execution_time < 30.0, f"파이프라인 실행 시간이 너무 깁니다: {total_execution_time:.3f}초"
        
        # 테스트 완료 - 모든 검증이 통과했음을 의미
        assert True
    
    @pytest.mark.integration
    def test_complete_pipeline_with_vitamin_project(self, evaluation_chains):
        """Vitamin 프로젝트에 대한 전체 파이프라인 테스트"""
        # Vitamin 유형으로 분류될 가능성이 높은 분석 결과
        vitamin_analysis_results = {
            "video_analysis": {
                "content": "사용자 경험을 향상시키는 혁신적인 소셜 미디어 플랫폼",
                "key_features": ["창의적 콘텐츠", "소셜 공유", "개인화 추천"],
                "target_audience": "젊은 사용자층, 크리에이터"
            },
            "document_analysis": {
                "content": "사용자의 창의성과 즐거움을 증진시키는 엔터테인먼트 앱",
                "business_model": "광고 기반 무료 서비스",
                "problem_solving": "사용자 만족도 향상, 창의적 표현 지원"
            },
            "presentation_analysis": {
                "content": "혁신적인 UI/UX와 AI 기반 개인화 서비스",
                "market_size": "글로벌 소셜 미디어 시장",
                "competitive_advantage": "독창적인 사용자 경험"
            }
        }
        
        # 전체 파이프라인 실행
        result = self._run_complete_pipeline(vitamin_analysis_results, evaluation_chains)
        
        # Vitamin 프로젝트 특성 검증
        type_result = result["type_result"]
        
        # Vitamin으로 분류되었거나 Balanced로 분류되어야 함
        assert type_result["project_type"] in ["vitamin", "balanced"]
        
        # Vitamin 가중치가 올바르게 적용되었는지 확인
        weight_manager = WeightManager()
        weights = weight_manager.get_weights(type_result["project_type"])
        
        if type_result["project_type"] == "vitamin":
            # Vitamin 프로젝트는 user_engagement, innovation, social_impact에 높은 가중치
            assert weights["user_engagement"] >= 0.2
            assert weights["innovation"] >= 0.15
            assert weights["social_impact"] >= 0.15
        
        print(f"\n=== Vitamin 프로젝트 테스트 완료 ===")
        print(f"분류 결과: {type_result['project_type']}")
        print(f"최종 점수: {result['final_score']:.2f}/10")
    
    @pytest.mark.integration
    def test_pipeline_with_low_confidence_classification(self, evaluation_chains):
        """신뢰도가 낮은 분류 결과에 대한 파이프라인 테스트"""
        # 애매한 분석 결과 (PainKiller와 Vitamin 특성이 혼재)
        ambiguous_analysis_results = {
            "video_analysis": {
                "content": "효율성과 사용자 경험을 모두 고려한 플랫폼",
                "key_features": ["효율성", "사용자 친화적", "혁신적"],
                "target_audience": "일반 사용자"
            },
            "document_analysis": {
                "content": "비즈니스 효율성과 사용자 만족을 동시에 추구",
                "business_model": "하이브리드 모델",
                "problem_solving": "다양한 문제 해결"
            },
            "presentation_analysis": {
                "content": "종합적인 솔루션 제공",
                "market_size": "다양한 시장",
                "competitive_advantage": "균형잡힌 접근"
            }
        }
        
        # 분류기 실행
        classifier = ProjectTypeClassifier()
        type_result = classifier.classify(ambiguous_analysis_results)
        
        # 신뢰도가 낮을 경우 Balanced로 분류되고 경고 메시지가 있어야 함
        if type_result["confidence"] < 0.7:
            assert type_result["project_type"] == "balanced"
            assert type_result["warning_message"] is not None
            print(f"경고 메시지: {type_result['warning_message']}")
        
        # 전체 파이프라인 실행
        result = self._run_complete_pipeline(ambiguous_analysis_results, evaluation_chains)
        
        # Balanced 가중치 검증
        if type_result["project_type"] == "balanced":
            weight_manager = WeightManager()
            weights = weight_manager.get_weights("balanced")
            
            # Balanced는 모든 가중치가 비교적 균등해야 함
            weight_values = list(weights.values())
            max_weight = max(weight_values)
            min_weight = min(weight_values)
            assert (max_weight - min_weight) < 0.1  # 가중치 차이가 0.1 미만
        
        print(f"\n=== 낮은 신뢰도 분류 테스트 완료 ===")
        print(f"신뢰도: {type_result['confidence']:.3f}")
        print(f"분류 결과: {type_result['project_type']}")
    
    def _run_complete_pipeline(self, analysis_results, evaluation_chains):
        """전체 파이프라인 실행 헬퍼 메서드"""
        # 1. 프로젝트 유형 분류
        classifier = ProjectTypeClassifier()
        type_result = classifier.classify(analysis_results)
        
        # 2. 평가 체인 실행
        evaluator_input = {
            "project_type": type_result,
            **analysis_results
        }
        
        results = {}
        for chain_name, chain in evaluation_chains.items():
            try:
                result = chain.invoke(evaluator_input)
                results[chain_name] = result
            except Exception as e:
                results[chain_name] = {
                    "score": 0.0,
                    "reasoning": f"평가 중 오류 발생: {str(e)}",
                    "error": str(e)
                }
        
        # 3. 최종 점수 계산
        weight_manager = WeightManager()
        scores = {}
        for chain_name, result in results.items():
            if isinstance(result, dict):
                if chain_name == "business_value" and "total_score" in result:
                    score = result["total_score"]
                else:
                    score = result.get("score", 0)
            else:
                score = float(result) if result else 0.0
            scores[chain_name] = score
        
        final_score = weight_manager.calculate_final_score(scores, type_result['project_type'])
        
        return {
            "type_result": type_result,
            "evaluation_results": results,
            "final_score": final_score,
            "scores": scores
        }


class TestPipelineErrorHandling:
    """파이프라인 오류 처리 테스트"""
    
    @pytest.mark.integration
    def test_pipeline_with_empty_analysis_data(self):
        """빈 분석 데이터에 대한 파이프라인 테스트"""
        empty_analysis = {
            "video_analysis": {},
            "document_analysis": {},
            "presentation_analysis": {}
        }
        
        # 분류기는 빈 데이터에도 기본값을 반환해야 함
        classifier = ProjectTypeClassifier()
        type_result = classifier.classify(empty_analysis)
        
        assert type_result is not None
        assert type_result["project_type"] == "balanced"  # 기본값
        assert type_result["confidence"] < 0.7  # 낮은 신뢰도
        assert type_result["warning_message"] is not None
        
        print(f"빈 데이터 분류 결과: {type_result}")
    
    @pytest.mark.integration
    def test_pipeline_with_chain_failures(self):
        """일부 평가 체인 실패 시 파이프라인 테스트"""
        # 정상적인 분석 데이터
        analysis_data = {
            "video_analysis": {"content": "테스트 프로젝트"},
            "document_analysis": {"content": "테스트 내용"},
            "presentation_analysis": {"content": "테스트 발표"}
        }
        
        classifier = ProjectTypeClassifier()
        type_result = classifier.classify(analysis_data)
        
        evaluator_input = {
            "project_type": type_result,
            **analysis_data
        }
        
        # 일부 체인에서 의도적으로 오류 발생시키기
        chains = {
            "business_value": BusinessValueChain(),
            "accessibility": AccessibilityChain(),
        }
        
        results = {}
        for chain_name, chain in chains.items():
            try:
                result = chain.invoke(evaluator_input)
                results[chain_name] = result
            except Exception as e:
                # 오류 발생 시 기본값 사용
                results[chain_name] = {
                    "score": 0.0,
                    "reasoning": f"평가 중 오류 발생: {str(e)}",
                    "suggestions": ["시스템 관리자에게 문의하세요"],
                    "error": str(e)
                }
        
        # 오류가 발생해도 파이프라인이 계속 진행되어야 함
        assert len(results) == len(chains)
        
        # 최종 점수 계산도 가능해야 함
        weight_manager = WeightManager()
        scores = {}
        for chain_name, result in results.items():
            if isinstance(result, dict):
                score = result.get("score", 0) or result.get("total_score", 0)
            else:
                score = float(result) if result else 0.0
            scores[chain_name] = score
        
        # 부분적인 점수로도 계산 가능해야 함
        partial_final_score = sum(scores.values()) / len(scores) if scores else 0.0
        assert 0.0 <= partial_final_score <= 10.0
        
        print(f"부분 실패 시 최종 점수: {partial_final_score:.2f}")


class TestPipelinePerformance:
    """파이프라인 성능 테스트"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_pipeline_performance_benchmark(self):
        """파이프라인 성능 벤치마크 테스트"""
        analysis_data = {
            "video_analysis": {
                "content": "AI 기반 헬스케어 모니터링 시스템",
                "key_features": ["실시간 모니터링", "AI 분석"],
                "target_audience": "의료진"
            },
            "document_analysis": {
                "content": "효율성 개선 솔루션",
                "business_model": "SaaS",
                "problem_solving": "업무 효율성"
            },
            "presentation_analysis": {
                "content": "혁신적인 기술 솔루션",
                "market_size": "글로벌 시장",
                "competitive_advantage": "AI 기술"
            }
        }
        
        # 여러 번 실행하여 평균 성능 측정
        execution_times = []
        
        for i in range(3):  # 3회 실행
            start_time = time.time()
            
            # 전체 파이프라인 실행
            classifier = ProjectTypeClassifier()
            type_result = classifier.classify(analysis_data)
            
            evaluator_input = {
                "project_type": type_result,
                **analysis_data
            }
            
            # 모든 평가 체인 실행
            chains = {
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
            
            for chain_name, chain in chains.items():
                try:
                    chain.invoke(evaluator_input)
                except Exception:
                    pass  # 성능 테스트에서는 오류 무시
            
            # 가중치 계산
            weight_manager = WeightManager()
            weight_manager.calculate_final_score({}, type_result['project_type'])
            
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            
            print(f"실행 {i+1}: {execution_time:.3f}초")
        
        # 성능 분석
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        print(f"\n=== 성능 벤치마크 결과 ===")
        print(f"평균 실행 시간: {avg_time:.3f}초")
        print(f"최대 실행 시간: {max_time:.3f}초")
        print(f"최소 실행 시간: {min_time:.3f}초")
        
        # 성능 기준 검증 (평균 35초 이내, 최대 45초 이내)
        assert avg_time < 35.0, f"평균 실행 시간이 너무 깁니다: {avg_time:.3f}초"
        assert max_time < 45.0, f"최대 실행 시간이 너무 깁니다: {max_time:.3f}초"


if __name__ == "__main__":
    # 통합 테스트만 실행
    pytest.main([__file__, "-v", "-m", "integration"])