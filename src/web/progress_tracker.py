# -*- coding: utf-8 -*-
"""
분석 진행 상황 추적기
"""
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class StepProgress:
    """단계별 진행 상황"""
    name: str
    status: str = "pending"  # pending, in_progress, completed, error
    progress: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class SessionProgress:
    """세션별 전체 진행 상황"""
    session_id: str
    overall_progress: float = 0.0
    status: str = "pending"  # pending, in_progress, completed, error
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    steps: Dict[str, StepProgress] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class ProgressTracker:
    """분석 진행 상황을 추적하는 클래스"""
    
    def __init__(self):
        self._sessions: Dict[str, SessionProgress] = {}
        self._lock = threading.Lock()
        
        # 기본 분석 단계들
        self.default_steps = [
            "파일 분석",
            "프로젝트 분류", 
            "평가 체인 실행",
            "최종 점수 계산"
        ]
    
    def initialize_progress(self, session_id: str) -> None:
        """세션의 진행 상황 초기화"""
        with self._lock:
            session_progress = SessionProgress(session_id=session_id)
            
            # 기본 단계들 초기화
            for step_name in self.default_steps:
                session_progress.steps[step_name] = StepProgress(name=step_name)
            
            session_progress.status = "in_progress"
            self._sessions[session_id] = session_progress
    
    def update_step(self, session_id: str, step_name: str, status: str, progress: float) -> None:
        """특정 단계의 진행 상황 업데이트"""
        with self._lock:
            if session_id not in self._sessions:
                self.initialize_progress(session_id)
            
            session = self._sessions[session_id]
            
            if step_name not in session.steps:
                session.steps[step_name] = StepProgress(name=step_name)
            
            step = session.steps[step_name]
            
            # 상태 변경 시 시간 기록
            if step.status != status:
                if status == "in_progress" and step.start_time is None:
                    step.start_time = datetime.now()
                elif status in ["completed", "error"]:
                    step.end_time = datetime.now()
            
            step.status = status
            step.progress = min(100.0, max(0.0, progress))
            
            # 전체 진행률 계산
            self._calculate_overall_progress(session_id)
    
    def add_error(self, session_id: str, error_message: str) -> None:
        """오류 메시지 추가"""
        with self._lock:
            if session_id not in self._sessions:
                self.initialize_progress(session_id)
            
            session = self._sessions[session_id]
            session.errors.append(f"[{datetime.now().strftime('%H:%M:%S')}] {error_message}")
            session.status = "error"
    
    def set_overall_progress(self, session_id: str, progress: float) -> None:
        """전체 진행률 직접 설정"""
        with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.overall_progress = min(100.0, max(0.0, progress))
                
                if progress >= 100.0:
                    session.status = "completed"
                    session.end_time = datetime.now()
    
    def _calculate_overall_progress(self, session_id: str) -> None:
        """전체 진행률 계산 (내부 메서드)"""
        if session_id not in self._sessions:
            return
        
        session = self._sessions[session_id]
        
        if not session.steps:
            session.overall_progress = 0.0
            return
        
        # 각 단계의 가중치 (동일하게 설정)
        step_weights = {
            "파일 분석": 0.3,
            "프로젝트 분류": 0.2,
            "평가 체인 실행": 0.4,
            "최종 점수 계산": 0.1
        }
        
        total_progress = 0.0
        total_weight = 0.0
        
        for step_name, step in session.steps.items():
            weight = step_weights.get(step_name, 1.0 / len(session.steps))
            total_weight += weight
            
            if step.status == "completed":
                total_progress += weight * 100.0
            elif step.status == "in_progress":
                total_progress += weight * step.progress
            # pending이나 error 상태는 0으로 계산
        
        if total_weight > 0:
            session.overall_progress = total_progress / total_weight
        else:
            session.overall_progress = 0.0
    
    def get_progress(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션의 진행 상황 조회"""
        with self._lock:
            if session_id not in self._sessions:
                return None
            
            session = self._sessions[session_id]
            
            # StepProgress 객체들을 딕셔너리로 변환
            steps_dict = {}
            for step_name, step in session.steps.items():
                steps_dict[step_name] = {
                    'name': step.name,
                    'status': step.status,
                    'progress': step.progress,
                    'start_time': step.start_time.isoformat() if step.start_time else None,
                    'end_time': step.end_time.isoformat() if step.end_time else None,
                    'error_message': step.error_message
                }
            
            return {
                'session_id': session.session_id,
                'overall_progress': session.overall_progress,
                'status': session.status,
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'steps': steps_dict,
                'errors': session.errors.copy(),
                'estimated_remaining_time': self._estimate_remaining_time(session)
            }
    
    def _estimate_remaining_time(self, session: SessionProgress) -> Optional[float]:
        """남은 시간 추정 (초 단위)"""
        if session.overall_progress <= 0:
            return None
        
        elapsed_time = (datetime.now() - session.start_time).total_seconds()
        
        if session.overall_progress >= 100:
            return 0.0
        
        # 현재 진행률을 기반으로 남은 시간 추정
        estimated_total_time = elapsed_time * (100.0 / session.overall_progress)
        remaining_time = estimated_total_time - elapsed_time
        
        return max(0.0, remaining_time)
    
    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """모든 세션의 진행 상황 조회"""
        with self._lock:
            result = {}
            for session_id in self._sessions:
                result[session_id] = self.get_progress(session_id)
            return result
    
    def cleanup_session(self, session_id: str) -> bool:
        """세션 정보 정리"""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """오래된 세션들 정리"""
        with self._lock:
            current_time = datetime.now()
            sessions_to_remove = []
            
            for session_id, session in self._sessions.items():
                session_age = (current_time - session.start_time).total_seconds() / 3600
                if session_age > max_age_hours:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self._sessions[session_id]
            
            return len(sessions_to_remove)
    
    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 요약 정보 조회"""
        progress_data = self.get_progress(session_id)
        if not progress_data:
            return None
        
        completed_steps = sum(1 for step in progress_data['steps'].values() 
                            if step['status'] == 'completed')
        total_steps = len(progress_data['steps'])
        
        return {
            'session_id': session_id,
            'overall_progress': progress_data['overall_progress'],
            'status': progress_data['status'],
            'completed_steps': completed_steps,
            'total_steps': total_steps,
            'error_count': len(progress_data['errors']),
            'estimated_remaining_time': progress_data['estimated_remaining_time']
        }