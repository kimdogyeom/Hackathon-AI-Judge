# -*- coding: utf-8 -*-
"""
가중치 관리자 모듈
프로젝트 유형별 평가 체인 가중치를 관리합니다.
"""

import logging
from enum import Enum
from typing import Dict, Optional
from .config_manager import get_config_manager

logger = logging.getLogger(__name__)


class ProjectType(Enum):
    """프로젝트 유형 열거형"""
    PAINKILLER = "painkiller"
    VITAMIN = "vitamin"
    BALANCED = "balanced"


class WeightManager:
    """
    프로젝트 유형별 가중치 관리 클래스
    config_manager를 사용하여 가중치를 조회합니다.
    """
    
    def __init__(self):
        """WeightManager 초기화"""
        self.config_manager = get_config_manager()
        self._default_chains = [
            'business_value', 'technical_feasibility', 'cost_analysis',
            'user_engagement', 'innovation', 'social_impact', 
            'sustainability', 'accessibility', 'network_effect'
        ]
    
    def get_weights(self, project_type: str) -> Dict[str, float]:
        """
        프로젝트 유형에 따른 가중치 반환
        
        :param project_type: 프로젝트 유형 ('painkiller', 'vitamin', 'balanced')
        :return: 체인별 가중치 딕셔너리
        """
        try:
            # 프로젝트 유형 정규화
            normalized_type = project_type.lower().strip()
            
            # config_manager를 통해 가중치 조회
            weights = self.config_manager.get_weights(normalized_type)
            
            # 가중치 검증 및 정규화
            weights = self._validate_and_normalize_weights(weights, normalized_type)
            
            logger.debug(f"가중치 조회 완료: {normalized_type} -> {weights}")
            return weights
            
        except Exception as e:
            logger.error(f"가중치 조회 실패 ({project_type}): {str(e)}")
            return self._get_default_weights()
    
    def get_weights_by_enum(self, project_type: ProjectType) -> Dict[str, float]:
        """
        ProjectType 열거형을 사용한 가중치 반환
        
        :param project_type: ProjectType 열거형
        :return: 체인별 가중치 딕셔너리
        """
        return self.get_weights(project_type.value)
    
    def _validate_and_normalize_weights(self, weights: Dict[str, float], project_type: str) -> Dict[str, float]:
        """
        가중치 검증 및 정규화
        
        :param weights: 원본 가중치
        :param project_type: 프로젝트 유형
        :return: 검증 및 정규화된 가중치
        """
        if not weights:
            logger.warning(f"가중치가 비어있음: {project_type}")
            return self._get_default_weights()
        
        # 필수 체인 확인
        missing_chains = set(self._default_chains) - set(weights.keys())
        if missing_chains:
            logger.warning(f"누락된 체인: {missing_chains}")
            for chain in missing_chains:
                weights[chain] = 0.0
        
        # 가중치 합계 계산
        total_weight = sum(weights.values())
        
        # 정규화 필요 여부 확인
        tolerance = self.config_manager.get_config(
            'chain_weights.yaml', 
            'default_settings.weight_sum_tolerance', 
            0.01
        )
        
        if abs(total_weight - 1.0) > tolerance:
            logger.info(f"가중치 정규화 수행: {total_weight} -> 1.0")
            if total_weight > 0:
                weights = {k: v / total_weight for k, v in weights.items()}
            else:
                logger.error("가중치 합계가 0입니다. 기본값 사용")
                return self._get_default_weights()
        
        # 개별 가중치 범위 검증
        min_weight = self.config_manager.get_config(
            'chain_weights.yaml', 
            'validation.min_weight', 
            0.0
        )
        max_weight = self.config_manager.get_config(
            'chain_weights.yaml', 
            'validation.max_weight', 
            1.0
        )
        
        for chain, weight in weights.items():
            if weight < min_weight or weight > max_weight:
                logger.warning(f"가중치 범위 초과: {chain}={weight}")
                weights[chain] = max(min_weight, min(weight, max_weight))
        
        return weights
    
    def _get_default_weights(self) -> Dict[str, float]:
        """
        기본 균등 가중치 반환
        
        :return: 균등 가중치 딕셔너리
        """
        equal_weight = 1.0 / len(self._default_chains)
        return {chain: equal_weight for chain in self._default_chains}
    
    def get_supported_project_types(self) -> list:
        """
        지원되는 프로젝트 유형 목록 반환
        
        :return: 프로젝트 유형 문자열 리스트
        """
        return [pt.value for pt in ProjectType]
    
    def is_valid_project_type(self, project_type: str) -> bool:
        """
        유효한 프로젝트 유형인지 확인
        
        :param project_type: 확인할 프로젝트 유형
        :return: 유효성 여부
        """
        return project_type.lower().strip() in self.get_supported_project_types()


# 전역 인스턴스
_weight_manager = None


def get_weight_manager() -> WeightManager:
    """
    WeightManager 전역 인스턴스 반환
    
    :return: WeightManager 인스턴스
    """
    global _weight_manager
    if _weight_manager is None:
        _weight_manager = WeightManager()
    return _weight_manager


# 편의 함수들
def get_weights(project_type: str) -> Dict[str, float]:
    """
    가중치 조회 편의 함수
    
    :param project_type: 프로젝트 유형
    :return: 체인별 가중치 딕셔너리
    """
    return get_weight_manager().get_weights(project_type)


def get_weights_by_enum(project_type: ProjectType) -> Dict[str, float]:
    """
    ProjectType 열거형을 사용한 가중치 조회 편의 함수
    
    :param project_type: ProjectType 열거형
    :return: 체인별 가중치 딕셔너리
    """
    return get_weight_manager().get_weights_by_enum(project_type)