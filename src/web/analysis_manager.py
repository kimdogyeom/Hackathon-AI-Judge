# -*- coding: utf-8 -*-
"""
분석 관리자 - 백그라운드에서 분석 작업을 수행
"""
import threading
import time
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import traceback

from src.analysis import VideoAnalysis, DocumentAnalysis, PresentationAnalysis
from src.classifier import ProjectTypeClassifier
from src.chain import (
    AccessibilityChain, BusinessValueChain, CostAnalysisChain,
    InnovationChain, NetworkEffectChain, SocialImpactChain,
    SustainabilityChain, TechnicalFeasibilityChain, UserEngagementChain
)
from src.config.config_manager import get_config_manager
from src.web.progress_tracker import ProgressTracker


class AnalysisManager:
    """분석 작업을 관리하는 클래스"""
    
    def __init__(self):
        self.progress_tracker = ProgressTracker()
        self.config_manager = get_config_manager()
        
        # 분석 체인들 초기화
        self.analysis_chains = {
            'video': VideoAnalysis(),
            'document': DocumentAnalysis(),
            'presentation': PresentationAnalysis()
        }
        
        # 평가 체인들 초기화
        self.evaluation_chains = {
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
        
        # 프로젝트 분류기
        self.classifier = ProjectTypeClassifier()
    
    def start_analysis(self, session_id: str, file_paths: Dict[str, str], 
                      callback: Optional[Callable] = None) -> None:
        """
        백그라운드에서 분석 시작
        
        Args:
            session_id: 세션 ID
            file_paths: 파일 경로들 (file_type -> file_path)
            callback: 분석 완료 시 호출될 콜백 함수
        """
        def analysis_worker():
            try:
                self._run_analysis(session_id, file_paths, callback)
            except Exception as e:
                self.progress_tracker.add_error(
                    session_id, 
                    f"분석 중 예상치 못한 오류 발생: {str(e)}"
                )
                print(f"Analysis error: {e}")
                print(traceback.format_exc())
        
        # 백그라운드 스레드에서 분석 실행
        analysis_thread = threading.Thread(target=analysis_worker, daemon=True)
        analysis_thread.start()
    
    def _run_analysis(self, session_id: str, file_paths: Dict[str, str], 
                     callback: Optional[Callable] = None) -> None:
        """실제 분석 수행"""
        
        # 진행 상황 초기화
        self.progress_tracker.initialize_progress(session_id)
        
        try:
            # 1단계: 파일 분석
            self.progress_tracker.update_step(session_id, "파일 분석", "in_progress", 0)
            analysis_results = self._analyze_files(session_id, file_paths)
            self.progress_tracker.update_step(session_id, "파일 분석", "completed", 100)
            
            # 2단계: 프로젝트 분류
            self.progress_tracker.update_step(session_id, "프로젝트 분류", "in_progress", 0)
            classification_result = self._classify_project(session_id, analysis_results)
            self.progress_tracker.update_step(session_id, "프로젝트 분류", "completed", 100)
            
            # 3단계: 평가 체인 실행
            self.progress_tracker.update_step(session_id, "평가 체인 실행", "in_progress", 0)
            evaluation_results = self._run_evaluation_chains(
                session_id, analysis_results, classification_result
            )
            self.progress_tracker.update_step(session_id, "평가 체인 실행", "completed", 100)
            
            # 4단계: 최종 점수 계산
            self.progress_tracker.update_step(session_id, "최종 점수 계산", "in_progress", 0)
            final_results = self._calculate_final_scores(
                session_id, evaluation_results, classification_result
            )
            self.progress_tracker.update_step(session_id, "최종 점수 계산", "completed", 100)
            
            # 전체 진행률 100% 완료
            self.progress_tracker.set_overall_progress(session_id, 100)
            
            # 콜백 호출
            if callback:
                callback(session_id, final_results)
                
        except Exception as e:
            error_msg = f"분석 중 오류 발생: {str(e)}"
            self.progress_tracker.add_error(session_id, error_msg)
            raise
    
    def _analyze_files(self, session_id: str, file_paths: Dict[str, str]) -> Dict[str, Any]:
        """파일들을 분석하여 결과 반환"""
        analysis_results = {}
        total_files = len(file_paths)
        
        for i, (file_type, file_path) in enumerate(file_paths.items()):
            try:
                progress = (i / total_files) * 100
                self.progress_tracker.update_step(session_id, "파일 분석", "in_progress", progress)
                
                if file_type == 'video':
                    # 동영상 분석 - 로컬 파일 처리를 위해 빈 URI로 처리 (실제로는 파일 경로 사용)
                    try:
                        result = self.analysis_chains['video'].invoke({"s3_uri": ""})
                        analysis_results['video_analysis'] = result
                    except Exception as e:
                        # 동영상 분석 실패 시 기본값 제공
                        analysis_results['video_analysis'] = {
                            'content': f'동영상 파일 분석 실패: {str(e)}',
                            'summary': '동영상 분석을 완료할 수 없습니다.',
                            'keywords': ['분석실패'],
                            'error': str(e)
                        }
                    
                elif file_type == 'document':
                    # 문서 분석 - 로컬 파일 처리를 위해 빈 URI로 처리
                    try:
                        result = self.analysis_chains['document'].invoke({"s3_uri": ""})
                        analysis_results['document_analysis'] = result
                    except Exception as e:
                        # 문서 분석 실패 시 기본값 제공
                        analysis_results['document_analysis'] = {
                            'content': f'문서 파일 분석 실패: {str(e)}',
                            'summary': '문서 분석을 완료할 수 없습니다.',
                            'keywords': ['분석실패'],
                            'error': str(e)
                        }
                    
                elif file_type == 'presentation':
                    # 발표자료 분석 - 로컬 파일 처리를 위해 빈 URI로 처리
                    try:
                        result = self.analysis_chains['presentation'].invoke({"s3_uri": ""})
                        analysis_results['presentation_analysis'] = result
                    except Exception as e:
                        # 발표자료 분석 실패 시 기본값 제공
                        analysis_results['presentation_analysis'] = {
                            'content': f'발표자료 파일 분석 실패: {str(e)}',
                            'summary': '발표자료 분석을 완료할 수 없습니다.',
                            'keywords': ['분석실패'],
                            'error': str(e)
                        }
                
                # 파일별 진행률 업데이트
                progress = ((i + 1) / total_files) * 100
                self.progress_tracker.update_step(session_id, "파일 분석", "in_progress", progress)
                
            except Exception as e:
                error_msg = f"{file_type} 파일 분석 중 오류: {str(e)}"
                self.progress_tracker.add_error(session_id, error_msg)
                # 오류가 발생해도 다른 파일 분석은 계속 진행
                analysis_results[f'{file_type}_analysis'] = {
                    'error': str(e),
                    'content': '',
                    'summary': '분석 실패',
                    'keywords': []
                }
        
        return analysis_results
    
    def _classify_project(self, session_id: str, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """프로젝트 분류 수행"""
        try:
            self.progress_tracker.update_step(session_id, "프로젝트 분류", "in_progress", 50)
            
            classification_result = self.classifier.classify(analysis_results)
            
            self.progress_tracker.update_step(session_id, "프로젝트 분류", "in_progress", 100)
            
            return classification_result
            
        except Exception as e:
            error_msg = f"프로젝트 분류 중 오류: {str(e)}"
            self.progress_tracker.add_error(session_id, error_msg)
            
            # 분류 실패시 예외 재발생 (기본값 설정하지 않음)
            raise RuntimeError(f"프로젝트 분류 실패: {str(e)}") from e
    
    def _run_evaluation_chains(self, session_id: str, analysis_results: Dict[str, Any], 
                              classification_result: Dict[str, Any]) -> Dict[str, Any]:
        """평가 체인들 실행"""
        evaluation_results = {}
        total_chains = len(self.evaluation_chains)
        
        # 평가 체인 입력 데이터 준비
        chain_input = {
            "project_type": classification_result,
            **analysis_results
        }
        
        for i, (chain_name, chain) in enumerate(self.evaluation_chains.items()):
            try:
                progress = (i / total_chains) * 100
                self.progress_tracker.update_step(session_id, "평가 체인 실행", "in_progress", progress)
                
                # 체인 실행
                result = chain.invoke(chain_input)
                evaluation_results[chain_name] = result
                
                # 진행률 업데이트
                progress = ((i + 1) / total_chains) * 100
                self.progress_tracker.update_step(session_id, "평가 체인 실행", "in_progress", progress)
                
            except Exception as e:
                error_msg = f"{chain_name} 평가 중 오류: {str(e)}"
                self.progress_tracker.add_error(session_id, error_msg)
                
                # 오류 발생 시 기본값 사용
                evaluation_results[chain_name] = {
                    "score": 0.0,
                    "reasoning": f"평가 중 오류 발생: {str(e)}",
                    "suggestions": ["시스템 관리자에게 문의하세요"],
                    "execution_time": 0.0,
                    "error": str(e)
                }
        
        return evaluation_results
    
    def _calculate_final_scores(self, session_id: str, evaluation_results: Dict[str, Any], 
                               classification_result: Dict[str, Any]) -> Dict[str, Any]:
        """최종 점수 계산"""
        try:
            self.progress_tracker.update_step(session_id, "최종 점수 계산", "in_progress", 25)
            
            # 점수 추출
            scores = {}
            for category, result in evaluation_results.items():
                if isinstance(result, dict):
                    if category == "business_value" and "total_score" in result:
                        score = result.get("total_score", 0)
                    else:
                        score = result.get("score", 0)
                else:
                    score = float(result) if result else 0.0
                scores[category] = score
            
            self.progress_tracker.update_step(session_id, "최종 점수 계산", "in_progress", 50)
            
            # 가중치 적용
            project_type = classification_result['project_type']
            weights = self.config_manager.get_weights(project_type)
            weighted_scores = {chain: score * weights.get(chain, 0) for chain, score in scores.items()}
            final_score = sum(weighted_scores.values())
            
            self.progress_tracker.update_step(session_id, "최종 점수 계산", "in_progress", 75)
            
            # 결과 구성
            final_results = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'classification': classification_result,
                'evaluation_results': evaluation_results,
                'scores': scores,
                'weights': weights,
                'weighted_scores': weighted_scores,
                'final_score': final_score,
                'project_type': project_type,
                'weight_summary': f"{project_type} 유형 가중치 적용됨"
            }
            
            self.progress_tracker.update_step(session_id, "최종 점수 계산", "in_progress", 100)
            
            return final_results
            
        except Exception as e:
            error_msg = f"최종 점수 계산 중 오류: {str(e)}"
            self.progress_tracker.add_error(session_id, error_msg)
            raise
    
    def get_analysis_status(self, session_id: str) -> Dict[str, Any]:
        """분석 상태 조회"""
        return self.progress_tracker.get_progress(session_id)
    
    def cancel_analysis(self, session_id: str) -> bool:
        """분석 취소 (현재는 단순히 진행 상황만 정리)"""
        try:
            self.progress_tracker.add_error(session_id, "사용자에 의해 분석이 취소되었습니다.")
            return True
        except Exception:
            return False