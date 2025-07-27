"""
설정 관리자 모듈

프로젝트 유형 평가 시스템의 설정 파일을 관리하고,
실시간 업데이트 및 오류 처리를 담당합니다.
"""

import yaml
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List

# 로깅 설정
logger = logging.getLogger(__name__)


class ConfigManager:
    """
    설정 관리자 클래스
    
    YAML 설정 파일들을 로드하고 실시간으로 모니터링하여
    변경사항을 자동으로 반영합니다.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        설정 관리자 초기화
        
        Args:
            config_dir: 설정 파일 디렉토리 경로 (기본값: src/config)
        """
        if config_dir is None:
            config_dir = Path(__file__).parent
        
        self.config_dir = Path(config_dir)
        self._configs = {}
        self._default_configs = {}
        self._file_observers = {}
        self._lock = threading.RLock()
        
        # 기본 설정값 정의
        self._setup_default_configs()
        
        # 설정 파일 로드
        self._load_all_configs()

        
    def _setup_default_configs(self):
        """기본 설정값 정의"""
        self._default_configs = {
            'chain_weights.yaml': {
                'weights': {
                    'painkiller': {
                        'business_value': 0.25,
                        'technical_feasibility': 0.20,
                        'cost_analysis': 0.20,
                        'user_engagement': 0.10,
                        'innovation': 0.10,
                        'social_impact': 0.05,
                        'sustainability': 0.05,
                        'accessibility': 0.03,
                        'network_effect': 0.02
                    },
                    'vitamin': {
                        'user_engagement': 0.25,
                        'innovation': 0.20,
                        'social_impact': 0.20,
                        'business_value': 0.10,
                        'sustainability': 0.10,
                        'accessibility': 0.05,
                        'technical_feasibility': 0.05,
                        'cost_analysis': 0.03,
                        'network_effect': 0.02
                    },
                    'balanced': {
                        'business_value': 0.12,
                        'technical_feasibility': 0.12,
                        'cost_analysis': 0.11,
                        'user_engagement': 0.12,
                        'innovation': 0.12,
                        'social_impact': 0.11,
                        'sustainability': 0.10,
                        'accessibility': 0.10,
                        'network_effect': 0.10
                    }
                },
                'default_settings': {
                    'weight_sum_tolerance': 0.01,
                    'default_project_type': 'balanced',
                    'log_weight_changes': True,
                    'log_normalization': True
                }
            },
            'project_classification.yaml': {
                'classification': {
                    'confidence_threshold': 0.7,
                    'painkiller_keywords': [
                        '문제 해결', '효율성 개선', '비용 절감', '생산성 향상',
                        'pain point', 'solution', 'efficiency', 'cost reduction'
                    ],
                    'vitamin_keywords': [
                        '사용자 경험', '혁신', '창의성', '즐거움',
                        'user experience', 'innovation', 'creativity', 'engagement'
                    ],
                    'keyword_weights': {
                        'high_impact': 1.0,
                        'medium_impact': 0.7,
                        'low_impact': 0.4
                    }
                }
            }
        }
    
    def _load_all_configs(self):
        """모든 설정 파일 로드"""
        # 기본 설정 파일들
        default_config_files = [
            'chain_weights.yaml',
            'project_classification.yaml',
            'evaluation.yaml',
            'system_prompts.yaml',
            'model_config.yaml'
        ]
        
        # 설정 디렉토리의 모든 YAML 파일 검색
        all_yaml_files = set()
        if self.config_dir.exists():
            for yaml_file in self.config_dir.glob('*.yaml'):
                all_yaml_files.add(yaml_file.name)
        
        # 기본 파일들과 발견된 파일들을 합쳐서 로드
        config_files = list(set(default_config_files) | all_yaml_files)
        
        for config_file in config_files:
            self._load_config_file(config_file)
    
    def _load_config_file(self, filename: str) -> bool:
        """
        개별 설정 파일 로드
        
        Args:
            filename: 설정 파일명
            
        Returns:
            bool: 로드 성공 여부
        """
        file_path = self.config_dir / filename
        
        try:
            with self._lock:
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)
                        
                    # 설정 검증 및 기본값 적용
                    validated_config = self._validate_and_fix_config(filename, config_data)
                    self._configs[filename] = validated_config
                    
                    logger.info(f"설정 파일 로드 완료: {filename}")
                    return True
                else:
                    # 파일이 없으면 기본값 사용
                    if filename in self._default_configs:
                        self._configs[filename] = self._default_configs[filename].copy()
                        logger.warning(f"설정 파일이 없어 기본값 사용: {filename}")
                        return True
                    else:
                        logger.error(f"설정 파일을 찾을 수 없음: {filename}")
                        return False
                        
        except yaml.YAMLError as e:
            logger.error(f"YAML 파싱 오류 ({filename}): {e}")
            self._use_default_config(filename)
            return False
        except Exception as e:
            logger.error(f"설정 파일 로드 오류 ({filename}): {e}")
            self._use_default_config(filename)
            return False
    
    def _validate_and_fix_config(self, filename: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        설정 데이터 검증 및 수정
        
        Args:
            filename: 설정 파일명
            config_data: 설정 데이터
            
        Returns:
            Dict[str, Any]: 검증된 설정 데이터
        """
        if filename == 'chain_weights.yaml':
            return self._validate_weight_config(config_data)
        elif filename == 'project_classification.yaml':
            return self._validate_classification_config(config_data)
        else:
            # 다른 설정 파일들은 기본 검증만 수행
            return config_data if config_data is not None else {}
    
    def _validate_weight_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """가중치 설정 검증"""
        if not config_data or 'weights' not in config_data:
            logger.warning("가중치 설정이 없어 기본값 사용")
            return self._default_configs['chain_weights.yaml'].copy()
        
        validated_config = config_data.copy()
        weights = validated_config['weights']
        
        # 각 프로젝트 유형별 가중치 검증
        for project_type in ['painkiller', 'vitamin', 'balanced']:
            if project_type not in weights:
                logger.warning(f"프로젝트 유형 '{project_type}' 가중치가 없어 기본값 사용")
                weights[project_type] = self._default_configs['chain_weights.yaml']['weights'][project_type].copy()
                continue
            
            # 가중치 합계 검증 및 정규화
            weight_sum = sum(weights[project_type].values())
            tolerance = validated_config.get('default_settings', {}).get('weight_sum_tolerance', 0.01)
            
            if abs(weight_sum - 1.0) > tolerance:
                logger.warning(f"프로젝트 유형 '{project_type}' 가중치 합계가 1.0이 아님 (현재: {weight_sum:.3f}). 정규화 수행")
                
                # 정규화
                if weight_sum > 0:
                    for chain_name in weights[project_type]:
                        weights[project_type][chain_name] /= weight_sum
                else:
                    logger.error(f"프로젝트 유형 '{project_type}' 가중치 합계가 0. 기본값 사용")
                    weights[project_type] = self._default_configs['chain_weights.yaml']['weights'][project_type].copy()
        
        return validated_config
    
    def _validate_classification_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """분류 설정 검증"""
        if not config_data or 'classification' not in config_data:
            logger.warning("분류 설정이 없어 기본값 사용")
            return self._default_configs['project_classification.yaml'].copy()
        
        validated_config = config_data.copy()
        classification = validated_config['classification']
        
        # 신뢰도 임계값 검증
        threshold = classification.get('confidence_threshold', 0.7)
        if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
            logger.warning(f"잘못된 신뢰도 임계값: {threshold}. 기본값 0.7 사용")
            classification['confidence_threshold'] = 0.7
        
        # 키워드 리스트 검증
        for keyword_type in ['painkiller_keywords', 'vitamin_keywords']:
            if keyword_type not in classification or not isinstance(classification[keyword_type], list):
                logger.warning(f"{keyword_type}가 없거나 잘못된 형식. 기본값 사용")
                classification[keyword_type] = self._default_configs['project_classification.yaml']['classification'][keyword_type].copy()
        
        return validated_config
    
    def _use_default_config(self, filename: str):
        """기본 설정 사용"""
        if filename in self._default_configs:
            with self._lock:
                self._configs[filename] = self._default_configs[filename].copy()
            logger.warning(f"오류로 인해 기본 설정 사용: {filename}")
        else:
            logger.error(f"기본 설정이 없음: {filename}")
    
    def _reload_config_file(self, file_path: str):
        """설정 파일 재로드"""
        filename = Path(file_path).name
        if filename.endswith('.yaml') and filename in self._configs:
            logger.info(f"설정 파일 변경 감지: {filename}")
            self._load_config_file(filename)
    
    def get_config(self, filename: str, key_path: Optional[str] = None) -> Any:
        """
        설정값 조회
        
        Args:
            filename: 설정 파일명
            key_path: 설정 키 경로 (예: 'weights.painkiller.business_value')
            
        Returns:
            Any: 설정값
        """
        with self._lock:
            if filename not in self._configs:
                logger.warning(f"설정 파일이 로드되지 않음: {filename}")
                return None
            
            config = self._configs[filename]
            
            if key_path is None:
                return config
            
            # 키 경로를 따라 설정값 탐색
            keys = key_path.split('.')
            current = config
            
            try:
                for key in keys:
                    current = current[key]
                return current
            except (KeyError, TypeError):
                logger.warning(f"설정 키를 찾을 수 없음: {filename}:{key_path}")
                return None
    
    def get_weights(self, project_type: str) -> Dict[str, float]:
        """
        프로젝트 유형별 가중치 조회
        
        Args:
            project_type: 프로젝트 유형
            
        Returns:
            Dict[str, float]: 평가 체인별 가중치
        """
        weights = self.get_config('chain_weights.yaml', f'weights.{project_type}')
        if weights is None:
            logger.warning(f"프로젝트 유형 '{project_type}' 가중치를 찾을 수 없음. balanced 사용")
            weights = self.get_config('chain_weights.yaml', 'weights.balanced')
        
        return weights or {}
    
    def get_classification_config(self) -> Dict[str, Any]:
        """분류 설정 조회"""
        return self.get_config('project_classification.yaml', 'classification') or {}
    
    def stop_watching(self):
        """파일 감시 중지"""
        if hasattr(self, 'observer') and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            logger.info("설정 파일 감시 중지")
    
    def __del__(self):
        """소멸자 - 파일 감시 정리"""
        try:
            self.stop_watching()
        except:
            pass


# 전역 설정 관리자 인스턴스 (싱글톤 패턴)
_config_manager = None
_config_manager_lock = threading.Lock()


def get_config_manager() -> ConfigManager:
    """
    설정 관리자 인스턴스 반환 (싱글톤 패턴)
    
    Returns:
        ConfigManager: 설정 관리자 인스턴스
    """
    global _config_manager
    
    if _config_manager is None:
        with _config_manager_lock:
            if _config_manager is None:
                _config_manager = ConfigManager()
    
    return _config_manager


def reload_all_configs():
    """모든 설정 파일 재로드"""
    config_manager = get_config_manager()
    config_manager._load_all_configs()
    logger.info("모든 설정 파일 재로드 완료")