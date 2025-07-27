"""
가중치 관리자 모듈

프로젝트 유형별 평가 체인 가중치를 관리하고 적용하는 클래스를 제공합니다.
"""

import os
import yaml
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Union
from enum import Enum

# 로깅 설정
logger = logging.getLogger(__name__)


class ProjectType(Enum):
    """프로젝트 유형 열거형"""
    PAINKILLER = "painkiller"
    VITAMIN = "vitamin"
    BALANCED = "balanced"


class WeightManager:
    """
    프로젝트 유형별 가중치 설정을 관리하는 클래스
    
    주요 기능:
    - YAML 설정 파일에서 가중치 로드
    - 가중치 정규화 및 검증
    - 프로젝트 유형별 가중치 반환
    - 점수에 가중치 적용
    """
    
    def __init__(self, config_path: Optional[str] = None, auto_reload: bool = True):
        """
        가중치 관리자 초기화
        
        Args:
            config_path: 설정 파일 경로 (기본값: src/config/chain_weights.yaml)
            auto_reload: 설정 파일 자동 재로드 활성화 여부
        """
        self.config_path = config_path or self._get_default_config_path()
        self.weights_config = {}
        self.default_settings = {}
        self.auto_reload = auto_reload
        self._file_watcher_thread = None
        self._stop_watcher = threading.Event()
        self._last_modified = 0
        
        self._load_config()
        
        # 자동 재로드 활성화
        if self.auto_reload:
            self._start_file_watcher()
    
    def _get_default_config_path(self) -> str:
        """기본 설정 파일 경로 반환"""
        config_dir = Path(__file__).parent
        return str(config_dir / "chain_weights.yaml")
    
    def _load_config(self) -> None:
        """
        YAML 설정 파일에서 가중치 설정을 로드
        
        Raises:
            FileNotFoundError: 설정 파일을 찾을 수 없는 경우
            ValueError: YAML 파싱 오류 또는 잘못된 설정값
        """
        try:
            # 파일 수정 시간 업데이트
            if os.path.exists(self.config_path):
                self._last_modified = os.path.getmtime(self.config_path)
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config:
                raise ValueError("설정 파일이 비어있습니다")
            
            # 가중치 설정 로드
            self.weights_config = config.get('weights', {})
            if not self.weights_config:
                raise ValueError("가중치 설정이 없습니다")
            
            # 기본 설정 로드
            self.default_settings = config.get('default_settings', {})
            
            # 가중치 검증 및 정규화
            self._validate_and_normalize_weights()
            
            logger.info(f"가중치 설정을 성공적으로 로드했습니다: {self.config_path}")
            
        except FileNotFoundError:
            logger.error(f"가중치 설정 파일을 찾을 수 없습니다: {self.config_path}")
            self._load_default_weights()
            
        except yaml.YAMLError as e:
            logger.error(f"YAML 파싱 오류: {e}")
            self._load_default_weights()
            
        except ValueError as e:
            # 가중치 검증 오류는 다시 발생시킴 (기본값으로 대체하지 않음)
            if "음수 가중치" in str(e) or "가중치 형식" in str(e):
                raise e
            logger.error(f"설정 검증 오류: {e}")
            self._load_default_weights()
            
        except Exception as e:
            logger.error(f"설정 로드 중 오류 발생: {e}")
            self._load_default_weights()
    
    def _load_default_weights(self) -> None:
        """기본 가중치 설정 로드 (설정 파일 로드 실패 시 사용)"""
        logger.warning("기본 가중치 설정을 사용합니다")
        
        # 균등 가중치로 설정
        default_weight = 1.0 / 9  # 9개 평가 체인
        chain_names = [
            "business_value", "technical_feasibility", "cost_analysis",
            "user_engagement", "innovation", "social_impact", 
            "sustainability", "accessibility", "network_effect"
        ]
        
        equal_weights = {chain: default_weight for chain in chain_names}
        
        self.weights_config = {
            "painkiller": equal_weights.copy(),
            "vitamin": equal_weights.copy(),
            "balanced": equal_weights.copy()
        }
        
        self.default_settings = {
            "weight_sum_tolerance": 0.01,
            "default_project_type": "balanced",
            "log_weight_changes": True,
            "log_normalization": True
        }
    
    def _validate_and_normalize_weights(self) -> None:
        """가중치 검증 및 정규화"""
        tolerance = self.default_settings.get("weight_sum_tolerance", 0.01)
        log_normalization = self.default_settings.get("log_normalization", True)
        
        for project_type, weights in self.weights_config.items():
            if not isinstance(weights, dict):
                raise ValueError(f"잘못된 가중치 형식: {project_type}")
            
            # 음수 가중치 검증 (정규화 전에 먼저 검증)
            for chain, weight in weights.items():
                if weight < 0:
                    raise ValueError(f"음수 가중치는 허용되지 않습니다: {project_type}.{chain} = {weight}")
            
            # 가중치 합계 계산
            weight_sum = sum(weights.values())
            
            # 가중치 합계가 1.0에서 벗어난 경우 정규화
            if abs(weight_sum - 1.0) > tolerance:
                if log_normalization:
                    logger.warning(
                        f"{project_type} 유형의 가중치 합계가 {weight_sum:.3f}입니다. "
                        f"1.0으로 정규화합니다."
                    )
                
                # 정규화 수행
                if weight_sum > 0:
                    normalized_weights = {
                        chain: weight / weight_sum 
                        for chain, weight in weights.items()
                    }
                    self.weights_config[project_type] = normalized_weights
                else:
                    raise ValueError(f"{project_type} 유형의 가중치 합계가 0입니다")
    
    def get_weights(self, project_type: Union[str, ProjectType]) -> Dict[str, float]:
        """
        프로젝트 유형에 따른 가중치 반환
        
        Args:
            project_type: 프로젝트 유형 ("painkiller", "vitamin", "balanced" 또는 ProjectType)
        
        Returns:
            Dict[str, float]: 평가 체인별 가중치 딕셔너리
        
        Raises:
            ValueError: 지원하지 않는 프로젝트 유형인 경우
        """
        # ProjectType enum을 문자열로 변환
        if isinstance(project_type, ProjectType):
            project_type = project_type.value
        
        if project_type not in self.weights_config:
            default_type = self.default_settings.get("default_project_type", "balanced")
            logger.warning(
                f"지원하지 않는 프로젝트 유형: {project_type}. "
                f"기본 유형 '{default_type}'을 사용합니다."
            )
            project_type = default_type
        
        return self.weights_config[project_type].copy()
    
    def apply_weights(self, scores: Dict[str, float], weights: Dict[str, float]) -> Dict[str, float]:
        """
        점수에 가중치를 적용하여 가중 점수 계산
        
        Args:
            scores: 평가 체인별 점수 딕셔너리 (예: {"business_value": 7.5, ...})
            weights: 평가 체인별 가중치 딕셔너리
        
        Returns:
            Dict[str, float]: 가중치가 적용된 점수 딕셔너리
        """
        weighted_scores = {}
        
        for chain_name, score in scores.items():
            weight = weights.get(chain_name, 0.0)
            weighted_score = score * weight
            weighted_scores[chain_name] = weighted_score
            
            logger.debug(f"{chain_name}: {score:.2f} * {weight:.3f} = {weighted_score:.3f}")
        
        return weighted_scores
    
    def calculate_final_score(self, scores: Dict[str, float], project_type: Union[str, ProjectType]) -> float:
        """
        프로젝트 유형에 맞는 가중치를 적용하여 최종 점수 계산
        
        Args:
            scores: 평가 체인별 점수 딕셔너리
            project_type: 프로젝트 유형
        
        Returns:
            float: 가중치가 적용된 최종 점수
        """
        weights = self.get_weights(project_type)
        weighted_scores = self.apply_weights(scores, weights)
        final_score = sum(weighted_scores.values())
        
        logger.info(f"최종 점수 계산 완료: {final_score:.2f} (유형: {project_type})")
        return final_score
    
    def get_available_project_types(self) -> list:
        """사용 가능한 프로젝트 유형 목록 반환"""
        return list(self.weights_config.keys())
    
    def _start_file_watcher(self) -> None:
        """설정 파일 변경 감지를 위한 백그라운드 스레드 시작"""
        if self._file_watcher_thread is not None:
            return
        
        self._file_watcher_thread = threading.Thread(
            target=self._watch_config_file,
            daemon=True,
            name="WeightManager-FileWatcher"
        )
        self._file_watcher_thread.start()
        logger.debug("설정 파일 감시 스레드를 시작했습니다")
    
    def _watch_config_file(self) -> None:
        """설정 파일 변경을 감지하고 자동으로 재로드"""
        while not self._stop_watcher.is_set():
            try:
                if os.path.exists(self.config_path):
                    current_modified = os.path.getmtime(self.config_path)
                    
                    # 파일이 수정된 경우 재로드
                    if current_modified > self._last_modified:
                        logger.info("설정 파일 변경이 감지되어 자동으로 재로드합니다")
                        self._load_config()
                
                # 1초마다 확인
                self._stop_watcher.wait(1.0)
                
            except Exception as e:
                logger.error(f"파일 감시 중 오류 발생: {e}")
                self._stop_watcher.wait(5.0)  # 오류 시 5초 대기
    
    def stop_file_watcher(self) -> None:
        """파일 감시 스레드 중지"""
        if self._file_watcher_thread is not None:
            self._stop_watcher.set()
            self._file_watcher_thread.join(timeout=2.0)
            self._file_watcher_thread = None
            logger.debug("설정 파일 감시 스레드를 중지했습니다")
    
    def reload_config(self) -> None:
        """설정 파일을 다시 로드 (실시간 업데이트 지원)"""
        logger.info("가중치 설정을 다시 로드합니다")
        self._load_config()
    
    def get_weight_summary(self, project_type: Union[str, ProjectType]) -> str:
        """
        프로젝트 유형별 가중치 요약 정보 반환
        
        Args:
            project_type: 프로젝트 유형
        
        Returns:
            str: 가중치 요약 문자열
        """
        weights = self.get_weights(project_type)
        
        # 가중치 순으로 정렬
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        
        summary_lines = [f"=== {project_type} 유형 가중치 ==="]
        for chain_name, weight in sorted_weights:
            percentage = weight * 100
            summary_lines.append(f"  {chain_name}: {weight:.3f} ({percentage:.1f}%)")
        
        return "\n".join(summary_lines)
    
    def __del__(self):
        """소멸자 - 파일 감시 스레드 정리"""
        try:
            self.stop_file_watcher()
        except:
            pass  # 소멸자에서는 예외를 무시