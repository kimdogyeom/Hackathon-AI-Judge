"""
단순한 설정 관리자

기본 기능만 제공:
- YAML 파일 로드
- 기본값 제공
- 키 경로 접근
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """단순한 설정 관리자"""
    
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            config_dir = Path(__file__).parent
        
        self.config_dir = Path(config_dir)
        self._configs = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """모든 YAML 파일 로드 (하위 디렉토리 포함)"""
        # 루트 디렉토리의 YAML 파일들
        for yaml_file in self.config_dir.glob('*.yaml'):
            self._load_yaml_file(yaml_file)
        
        # settings 하위 디렉토리의 YAML 파일들
        settings_dir = self.config_dir / 'settings'
        if settings_dir.exists():
            for yaml_file in settings_dir.rglob('*.yaml'):
                self._load_yaml_file(yaml_file)
    
    def _load_yaml_file(self, yaml_file):
        """개별 YAML 파일 로드"""
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
            self._configs[yaml_file.name] = config_data
            logger.debug(f"설정 로드: {yaml_file.name}")
        except Exception as e:
            logger.warning(f"설정 로드 실패 {yaml_file.name}: {e}")
            self._configs[yaml_file.name] = {}
    
    def get_config(self, filename: str, key_path: Optional[str] = None, default: Any = None) -> Any:
        """설정값 조회"""
        if filename not in self._configs:
            logger.warning(f"설정 파일 없음: {filename}")
            return default
        
        config = self._configs[filename]
        
        if key_path is None:
            return config
        
        # 키 경로 탐색
        current = config
        for key in key_path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def get_weights(self, project_type: str) -> Dict[str, float]:
        """가중치 조회 (weight_manager 대체)"""
        weights = self.get_config('chain_weights.yaml', f'weights.{project_type}', {})
        if not weights:
            # 기본 균등 가중치
            chains = ['business_value', 'technical_feasibility', 'cost_analysis',
                     'user_engagement', 'innovation', 'social_impact', 
                     'sustainability', 'accessibility', 'network_effect']
            weights = {chain: 1.0/len(chains) for chain in chains}
        return weights


# 전역 인스턴스
_config_manager = None

def get_config_manager():
    """설정 관리자 인스턴스 반환"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


# 편의 함수들
def get_config(filename: str, key_path: Optional[str] = None, default: Any = None):
    """설정값 조회 편의 함수"""
    return get_config_manager().get_config(filename, key_path, default)

def get_weights(project_type: str):
    """가중치 조회 편의 함수"""
    return get_config_manager().get_weights(project_type)

def get_system_prompt(analysis_type: str):
    """시스템 프롬프트 조회"""
    prompts = get_config('system_prompts.yaml', analysis_type, {})
    return prompts.get('system_prompt', '')