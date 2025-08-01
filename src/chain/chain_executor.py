# -*- coding: utf-8 -*-
"""
체인 실행기 모듈 - 다양한 평가 체인을 관리하고 실행합니다.
"""

import time
from typing import Dict, Any, List, Optional, Tuple

from .base_evaluation_chain import EvaluationChainBase
from .accessibility_chain import AccessibilityChain
from .business_value_chain import BusinessValueChain
from .cost_analysis_chain import CostAnalysisChain
from .innovation_chain import InnovationChain
from .network_effect_chain import NetworkEffectChain
from .social_impact_chain import SocialImpactChain
from .sustainability_chain import SustainabilityChain
from .technical_feasibility_chain import TechnicalFeasibilityChain
from .user_engagement_chain import UserEngagementChain


class ChainExecutor:
    """
    평가 체인의 실행을 관리하는 실행기 클래스.
    
    다양한 평가 체인들을 생성, 관리하고 일괄 실행합니다.
    결과를 취합하여 통합된 평가 결과를 제공합니다.
    """
    
    def __init__(self):
        """
        체인 실행기 초기화
        """
        # 기본 체인 객체들 초기화
        self.chains = {
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
        
        # 진행 상황 콜백 함수 (기본값은 None)
        self.progress_callback = None
    
    def set_progress_callback(self, callback_fn) -> None:
        """
        진행 상황을 업데이트할 콜백 함수 설정
        
        Args:
            callback_fn: 진행 상황을 받을 콜백 함수 (chain_name, step, total_steps)
        """
        self.progress_callback = callback_fn
    
    def execute_all(self, chain_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        모든 평가 체인 실행
        
        Args:
            chain_input: 모든 체인에 전달할 입력 데이터
            
        Returns:
            Dict: 표준화된 체인 실행 결과
        """
        total_start_time = time.time()
        chain_results = {}
        error_count = 0
        total_chains = len(self.chains)
        
        # 각 체인을 순차적으로 실행
        for i, (chain_name, chain) in enumerate(self.chains.items()):
            # 콜백이 설정된 경우 진행 상황 업데이트
            if self.progress_callback:
                self.progress_callback(chain_name, i, total_chains)
            
            chain_start_time = time.time()
            
            try:
                # 체인 실행
                result = chain.invoke(chain_input)
                
                # 표준화된 응답 구조 검증 및 정리
                standardized_result = self._standardize_chain_result(result, chain_name)
                standardized_result["execution_time"] = time.time() - chain_start_time
                
                chain_results[chain_name] = standardized_result
                
            except Exception as e:
                error_count += 1
                # 오류 발생 시 표준화된 기본값
                chain_results[chain_name] = {
                    "score": 5.0,
                    "reasoning": f"평가 중 오류 발생: {str(e)}",
                    "suggestions": ["시스템 관리자에게 문의하세요"],
                    "project_type": chain_input.get("project_type", "balanced"),
                    "evaluation_method": "error_fallback",
                    "execution_time": time.time() - chain_start_time,
                    "error": str(e)
                }
        
        # 전체 실행 시간 기록
        total_execution_time = time.time() - total_start_time
        
        # 결과 요약 생성
        summary = self._generate_execution_summary(chain_results)
        
        # 메타데이터 추가
        metadata = {
            "total_execution_time": total_execution_time,
            "error_count": error_count,
            "completed_chains": total_chains - error_count,
            "total_chains": total_chains,
            "average_score": self.get_average_score(chain_results),
            "project_type": chain_input.get("project_type", "balanced")
        }
        
        # 최종 결과 구성
        final_results = {
            "chain_results": chain_results,
            "summary": summary,
            "metadata": metadata
        }
        
        return final_results
    
    def get_scores(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """
        체인 실행 결과에서 점수 추출
        
        Args:
            results: 체인 실행 결과 (표준화된 구조)
            
        Returns:
            Dict: 체인별 점수
        """
        scores = {}
        
        for chain_name, result in results.items():
            if isinstance(result, dict):
                score = result.get("score", 5.0)
                # None 값을 기본값으로 변환
                if score is None:
                    score = 5.0
                # 점수 범위 검증
                score = max(0.0, min(10.0, float(score)))
            else:
                score = 5.0  # 기본값
            scores[chain_name] = score
        
        return scores
    
    def get_chain_details(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        체인별 상세 정보 추출 (점수, 근거, 제안사항 분리)
        
        Args:
            results: 체인 실행 결과
            
        Returns:
            Dict: 체인별 상세 정보
        """
        details = {}
        
        for chain_name, result in results.items():
            if isinstance(result, dict):
                details[chain_name] = {
                    "score": result.get("score", 5.0),
                    "reasoning": result.get("reasoning", "평가 근거가 제공되지 않았습니다."),
                    "suggestions": result.get("suggestions", []),
                    "project_type": result.get("project_type", "balanced"),
                    "evaluation_method": result.get("evaluation_method", chain_name),
                    "execution_time": result.get("execution_time", 0.0)
                }
            else:
                # 레거시 결과 처리
                details[chain_name] = {
                    "score": float(result) if result else 5.0,
                    "reasoning": "레거시 결과 - 상세 정보 없음",
                    "suggestions": [],
                    "project_type": "balanced",
                    "evaluation_method": chain_name,
                    "execution_time": 0.0
                }
        
        return details
    
    def generate_comprehensive_report(self, execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        종합적인 평가 리포트 생성
        
        Args:
            execution_results: execute_all()의 결과
            
        Returns:
            Dict: 종합 평가 리포트
        """
        chain_results = execution_results.get("chain_results", {})
        summary = execution_results.get("summary", {})
        metadata = execution_results.get("metadata", {})
        
        # 프로젝트 타입별 분석
        project_type = metadata.get("project_type", "balanced")
        project_analysis = self._analyze_by_project_type(chain_results, project_type)
        
        # 강점과 약점 분석
        strengths_weaknesses = self._analyze_strengths_weaknesses(chain_results)
        
        # 우선순위별 개선사항
        prioritized_suggestions = self._prioritize_suggestions(chain_results)
        
        # 체인별 상세 분석
        detailed_analysis = self._generate_detailed_chain_analysis(chain_results)
        
        return {
            "executive_summary": {
                "overall_score": summary.get("average_score", 5.0),
                "project_type": project_type,
                "evaluation_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_chains_evaluated": metadata.get("completed_chains", 0),
                "evaluation_status": "완료" if metadata.get("error_count", 0) == 0 else f"부분 완료 ({metadata.get('error_count', 0)}개 오류)"
            },
            "project_type_analysis": project_analysis,
            "performance_overview": {
                "strengths": strengths_weaknesses["strengths"],
                "weaknesses": strengths_weaknesses["weaknesses"],
                "score_distribution": summary.get("scores", {}),
                "highest_scoring_area": summary.get("highest_scoring_chain", {}),
                "lowest_scoring_area": summary.get("lowest_scoring_chain", {})
            },
            "improvement_recommendations": {
                "high_priority": prioritized_suggestions["high"],
                "medium_priority": prioritized_suggestions["medium"],
                "low_priority": prioritized_suggestions["low"],
                "total_suggestions": summary.get("total_suggestions", 0)
            },
            "detailed_chain_analysis": detailed_analysis,
            "execution_metadata": metadata
        }
    
    def _analyze_by_project_type(self, chain_results: Dict[str, Dict[str, Any]], project_type: str) -> Dict[str, Any]:
        """
        프로젝트 타입별 분석 수행
        
        Args:
            chain_results: 체인 실행 결과
            project_type: 프로젝트 타입
            
        Returns:
            Dict: 프로젝트 타입별 분석 결과
        """
        scores = {name: result["score"] for name, result in chain_results.items()}
        
        # 프로젝트 타입별 중요 영역 정의
        type_focus_areas = {
            "painkiller": ["business_value", "technical_feasibility", "cost_analysis"],
            "vitamin": ["user_engagement", "innovation", "social_impact"],
            "balanced": list(scores.keys())
        }
        
        focus_areas = type_focus_areas.get(project_type, list(scores.keys()))
        focus_scores = {area: scores.get(area, 5.0) for area in focus_areas if area in scores}
        
        if focus_scores:
            focus_average = sum(focus_scores.values()) / len(focus_scores)
        else:
            focus_average = 5.0
        
        # 타입별 권장사항
        type_recommendations = {
            "painkiller": [
                "핵심 문제 해결 능력 강화에 집중하세요",
                "기술적 실현가능성과 비용 효율성을 우선적으로 검토하세요",
                "명확한 비즈니스 가치 제안을 구체화하세요"
            ],
            "vitamin": [
                "사용자 경험과 혁신성 향상에 집중하세요",
                "사회적 영향과 장기적 가치 창출을 고려하세요",
                "사용자 참여도를 높이는 방안을 모색하세요"
            ],
            "balanced": [
                "모든 평가 영역의 균형잡힌 발전을 추구하세요",
                "약점 영역을 우선적으로 개선하세요",
                "강점 영역을 활용한 시너지 효과를 모색하세요"
            ]
        }
        
        return {
            "project_type": project_type,
            "focus_areas": focus_areas,
            "focus_area_scores": focus_scores,
            "focus_area_average": round(focus_average, 2),
            "type_specific_recommendations": type_recommendations.get(project_type, []),
            "alignment_assessment": self._assess_type_alignment(scores, project_type)
        }
    
    def _assess_type_alignment(self, scores: Dict[str, float], project_type: str) -> str:
        """
        프로젝트 타입과 평가 결과의 일치도 평가
        
        Args:
            scores: 체인별 점수
            project_type: 프로젝트 타입
            
        Returns:
            str: 일치도 평가 결과
        """
        if project_type == "painkiller":
            key_scores = [scores.get("business_value", 5), scores.get("technical_feasibility", 5)]
            avg_key = sum(key_scores) / len(key_scores)
            if avg_key >= 7:
                return "프로젝트가 Pain Killer 특성에 잘 부합합니다"
            elif avg_key >= 5:
                return "Pain Killer 특성이 어느 정도 나타나지만 개선이 필요합니다"
            else:
                return "Pain Killer 특성이 부족합니다. 핵심 문제 해결 능력을 강화하세요"
        
        elif project_type == "vitamin":
            key_scores = [scores.get("user_engagement", 5), scores.get("innovation", 5)]
            avg_key = sum(key_scores) / len(key_scores)
            if avg_key >= 7:
                return "프로젝트가 Vitamin 특성에 잘 부합합니다"
            elif avg_key >= 5:
                return "Vitamin 특성이 어느 정도 나타나지만 개선이 필요합니다"
            else:
                return "Vitamin 특성이 부족합니다. 사용자 경험과 혁신성을 강화하세요"
        
        else:  # balanced
            avg_all = sum(scores.values()) / len(scores) if scores else 5
            if avg_all >= 7:
                return "모든 영역에서 균형잡힌 우수한 성과를 보입니다"
            elif avg_all >= 5:
                return "전반적으로 균형잡힌 성과이지만 일부 영역의 개선이 필요합니다"
            else:
                return "여러 영역에서 개선이 필요합니다. 약점 영역을 우선적으로 보완하세요"
    
    def _analyze_strengths_weaknesses(self, chain_results: Dict[str, Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        강점과 약점 분석
        
        Args:
            chain_results: 체인 실행 결과
            
        Returns:
            Dict: 강점과 약점 분석 결과
        """
        scores = {name: result["score"] for name, result in chain_results.items()}
        
        # 점수 기준으로 강점/약점 분류
        strengths = []
        weaknesses = []
        
        for chain_name, score in scores.items():
            chain_data = {
                "area": chain_name,
                "score": score,
                "reasoning": chain_results[chain_name].get("reasoning", "")
            }
            
            if score >= 7.0:
                strengths.append(chain_data)
            elif score <= 4.0:
                weaknesses.append(chain_data)
        
        # 점수 순으로 정렬
        strengths.sort(key=lambda x: x["score"], reverse=True)
        weaknesses.sort(key=lambda x: x["score"])
        
        return {
            "strengths": strengths,
            "weaknesses": weaknesses
        }
    
    def _prioritize_suggestions(self, chain_results: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        개선사항을 우선순위별로 분류
        
        Args:
            chain_results: 체인 실행 결과
            
        Returns:
            Dict: 우선순위별 개선사항
        """
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for chain_name, result in chain_results.items():
            score = result.get("score", 5.0)
            suggestions = result.get("suggestions", [])
            
            for suggestion in suggestions:
                if score <= 4.0:  # 낮은 점수 영역의 제안사항은 고우선순위
                    high_priority.append(f"[{chain_name}] {suggestion}")
                elif score <= 6.0:  # 중간 점수 영역은 중우선순위
                    medium_priority.append(f"[{chain_name}] {suggestion}")
                else:  # 높은 점수 영역은 저우선순위
                    low_priority.append(f"[{chain_name}] {suggestion}")
        
        return {
            "high": high_priority,
            "medium": medium_priority,
            "low": low_priority
        }
    
    def _generate_detailed_chain_analysis(self, chain_results: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        체인별 상세 분석 생성
        
        Args:
            chain_results: 체인 실행 결과
            
        Returns:
            Dict: 체인별 상세 분석
        """
        detailed_analysis = {}
        
        for chain_name, result in chain_results.items():
            score = result.get("score", 5.0)
            
            # 점수 등급 분류
            if score >= 8.0:
                grade = "우수"
                grade_description = "매우 높은 수준의 성과"
            elif score >= 6.0:
                grade = "양호"
                grade_description = "적절한 수준의 성과"
            elif score >= 4.0:
                grade = "보통"
                grade_description = "개선이 필요한 수준"
            else:
                grade = "미흡"
                grade_description = "즉시 개선이 필요한 수준"
            
            detailed_analysis[chain_name] = {
                "score": score,
                "grade": grade,
                "grade_description": grade_description,
                "reasoning": result.get("reasoning", ""),
                "suggestions": result.get("suggestions", []),
                "evaluation_method": result.get("evaluation_method", ""),
                "execution_time": result.get("execution_time", 0.0),
                "project_type_applied": result.get("project_type", "balanced")
            }
        
        return detailed_analysis
    
    def _standardize_chain_result(self, result: Dict[str, Any], chain_name: str) -> Dict[str, Any]:
        """
        체인 결과를 표준화된 구조로 변환
        
        Args:
            result: 원본 체인 결과
            chain_name: 체인 이름
            
        Returns:
            Dict: 표준화된 결과
        """
        # 필수 필드 검증 및 기본값 설정
        standardized = {
            "score": float(result.get("score", 5.0)),
            "reasoning": str(result.get("reasoning", "평가 근거가 제공되지 않았습니다.")),
            "suggestions": result.get("suggestions", []),
            "project_type": result.get("project_type", "balanced"),
            "evaluation_method": result.get("evaluation_method", chain_name),
            "chain_name": chain_name
        }
        
        # 점수 범위 검증 (0-10)
        if standardized["score"] < 0:
            standardized["score"] = 0.0
        elif standardized["score"] > 10:
            standardized["score"] = 10.0
        
        # suggestions가 리스트가 아닌 경우 변환
        if not isinstance(standardized["suggestions"], list):
            if isinstance(standardized["suggestions"], str):
                standardized["suggestions"] = [standardized["suggestions"]]
            else:
                standardized["suggestions"] = []
        
        # 체인별 추가 데이터 보존
        chain_specific_data = {}
        for key, value in result.items():
            if key not in ["score", "reasoning", "suggestions", "project_type", "evaluation_method"]:
                chain_specific_data[key] = value
        
        if chain_specific_data:
            standardized["chain_specific_data"] = chain_specific_data
        
        return standardized
    
    def _generate_execution_summary(self, chain_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        체인 실행 결과 요약 생성
        
        Args:
            chain_results: 표준화된 체인 결과들
            
        Returns:
            Dict: 실행 요약
        """
        if not chain_results:
            return {
                "scores": {},
                "average_score": 5.0,
                "highest_scoring_chain": None,
                "lowest_scoring_chain": None,
                "total_suggestions": 0
            }
        
        # 점수 추출
        scores = {name: result["score"] for name, result in chain_results.items()}
        
        # 통계 계산
        average_score = sum(scores.values()) / len(scores)
        highest_scoring_chain = max(scores.items(), key=lambda x: x[1])
        lowest_scoring_chain = min(scores.items(), key=lambda x: x[1])
        
        # 전체 제안사항 수 계산
        total_suggestions = sum(len(result.get("suggestions", [])) for result in chain_results.values())
        
        return {
            "scores": scores,
            "average_score": round(average_score, 2),
            "highest_scoring_chain": {
                "name": highest_scoring_chain[0],
                "score": highest_scoring_chain[1]
            },
            "lowest_scoring_chain": {
                "name": lowest_scoring_chain[0],
                "score": lowest_scoring_chain[1]
            },
            "total_suggestions": total_suggestions
        }
    
    def get_average_score(self, results: Dict[str, Dict[str, Any]]) -> float:
        """
        모든 체인의 평균 점수 계산 (가중치 없이)
        
        Args:
            results: 체인 실행 결과
            
        Returns:
            float: 평균 점수 (0-10 범위)
        """
        scores = self.get_scores(results)
        if not scores:
            return 5.0  # 기본값
        
        return round(sum(scores.values()) / len(scores), 2)
    
    def generate_text_report(self, execution_results: Dict[str, Any]) -> str:
        """
        텍스트 형태의 종합 평가 리포트 생성
        
        Args:
            execution_results: execute_all()의 결과
            
        Returns:
            str: 텍스트 형태의 리포트
        """
        report = self.generate_comprehensive_report(execution_results)
        
        text_lines = []
        text_lines.append("=" * 80)
        text_lines.append("프로젝트 평가 종합 리포트")
        text_lines.append("=" * 80)
        text_lines.append("")
        
        # 요약 정보
        exec_summary = report["executive_summary"]
        text_lines.append("📊 평가 요약")
        text_lines.append("-" * 40)
        text_lines.append(f"전체 점수: {exec_summary['overall_score']}/10")
        text_lines.append(f"프로젝트 타입: {exec_summary['project_type']}")
        text_lines.append(f"평가 일시: {exec_summary['evaluation_date']}")
        text_lines.append(f"평가 상태: {exec_summary['evaluation_status']}")
        text_lines.append("")
        
        # 프로젝트 타입별 분석
        type_analysis = report["project_type_analysis"]
        text_lines.append("🎯 프로젝트 타입별 분석")
        text_lines.append("-" * 40)
        text_lines.append(f"타입: {type_analysis['project_type']}")
        text_lines.append(f"중점 영역 평균 점수: {type_analysis['focus_area_average']}/10")
        text_lines.append(f"타입 일치도: {type_analysis['alignment_assessment']}")
        text_lines.append("")
        text_lines.append("타입별 권장사항:")
        for rec in type_analysis['type_specific_recommendations']:
            text_lines.append(f"  • {rec}")
        text_lines.append("")
        
        # 성과 개요
        performance = report["performance_overview"]
        text_lines.append("📈 성과 개요")
        text_lines.append("-" * 40)
        
        if performance["strengths"]:
            text_lines.append("강점 영역:")
            for strength in performance["strengths"]:
                text_lines.append(f"  • {strength['area']}: {strength['score']}/10")
        
        if performance["weaknesses"]:
            text_lines.append("약점 영역:")
            for weakness in performance["weaknesses"]:
                text_lines.append(f"  • {weakness['area']}: {weakness['score']}/10")
        
        text_lines.append("")
        text_lines.append(f"최고 점수 영역: {performance['highest_scoring_area'].get('name', 'N/A')} ({performance['highest_scoring_area'].get('score', 0)}/10)")
        text_lines.append(f"최저 점수 영역: {performance['lowest_scoring_area'].get('name', 'N/A')} ({performance['lowest_scoring_area'].get('score', 0)}/10)")
        text_lines.append("")
        
        # 개선 권장사항
        improvements = report["improvement_recommendations"]
        text_lines.append("🔧 개선 권장사항")
        text_lines.append("-" * 40)
        
        if improvements["high_priority"]:
            text_lines.append("🔴 고우선순위:")
            for item in improvements["high_priority"]:
                text_lines.append(f"  • {item}")
            text_lines.append("")
        
        if improvements["medium_priority"]:
            text_lines.append("🟡 중우선순위:")
            for item in improvements["medium_priority"]:
                text_lines.append(f"  • {item}")
            text_lines.append("")
        
        if improvements["low_priority"]:
            text_lines.append("🟢 저우선순위:")
            for item in improvements["low_priority"]:
                text_lines.append(f"  • {item}")
            text_lines.append("")
        
        # 상세 분석
        detailed = report["detailed_chain_analysis"]
        text_lines.append("📋 영역별 상세 분석")
        text_lines.append("-" * 40)
        
        for chain_name, analysis in detailed.items():
            text_lines.append(f"\n[{chain_name.upper()}]")
            text_lines.append(f"점수: {analysis['score']}/10 ({analysis['grade']} - {analysis['grade_description']})")
            text_lines.append(f"평가 근거: {analysis['reasoning']}")
            if analysis['suggestions']:
                text_lines.append("개선사항:")
                for suggestion in analysis['suggestions']:
                    text_lines.append(f"  • {suggestion}")
        
        text_lines.append("")
        text_lines.append("=" * 80)
        text_lines.append("리포트 생성 완료")
        text_lines.append("=" * 80)
        
        return "\n".join(text_lines)