"""
가중치 관리자 테스트 모듈
"""

import pytest
import tempfile
import os
import yaml
from unittest.mock import patch, mock_open
from src.config.weight_manager import WeightManager, ProjectType


class TestWeightManager:
    """WeightManager 클래스 테스트"""
    
    @pytest.fixture
    def sample_config(self):
        """테스트용 샘플 설정"""
        return {
            'weights': {
                'painkiller': {
                    'business_value': 0.3,
                    'technical_feasibility': 0.3,
                    'cost_analysis': 0.2,
                    'user_engagement': 0.1,
                    'innovation': 0.1
                },
                'vitamin': {
                    'user_engagement': 0.4,
                    'innovation': 0.3,
                    'business_value': 0.2,
                    'technical_feasibility': 0.05,
                    'cost_analysis': 0.05
                },
                'balanced': {
                    'business_value': 0.2,
                    'technical_feasibility': 0.2,
                    'cost_analysis': 0.2,
                    'user_engagement': 0.2,
                    'innovation': 0.2
                }
            },
            'default_settings': {
                'weight_sum_tolerance': 0.01,
                'default_project_type': 'balanced',
                'log_weight_changes': True,
                'log_normalization': True
            }
        }
    
    @pytest.fixture
    def temp_config_file(self, sample_config):
        """임시 설정 파일 생성"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_config, f, default_flow_style=False, allow_unicode=True)
            temp_path = f.name
        
        yield temp_path
        
        # 정리
        os.unlink(temp_path)
    
    def test_init_with_valid_config(self, temp_config_file):
        """유효한 설정 파일로 초기화 테스트"""
        manager = WeightManager(temp_config_file)
        
        assert manager.config_path == temp_config_file
        assert 'painkiller' in manager.weights_config
        assert 'vitamin' in manager.weights_config
        assert 'balanced' in manager.weights_config
    
    def test_init_with_invalid_config_path(self):
        """존재하지 않는 설정 파일로 초기화 테스트"""
        manager = WeightManager('/nonexistent/path.yaml')
        
        # 기본 가중치가 로드되어야 함
        assert len(manager.weights_config) == 3
        assert 'painkiller' in manager.weights_config
    
    def test_get_weights_with_string(self, temp_config_file):
        """문자열 프로젝트 유형으로 가중치 조회 테스트"""
        manager = WeightManager(temp_config_file)
        
        weights = manager.get_weights('painkiller')
        
        assert isinstance(weights, dict)
        assert weights['business_value'] == 0.3
        assert weights['technical_feasibility'] == 0.3
    
    def test_get_weights_with_enum(self, temp_config_file):
        """ProjectType enum으로 가중치 조회 테스트"""
        manager = WeightManager(temp_config_file)
        
        weights = manager.get_weights(ProjectType.VITAMIN)
        
        assert isinstance(weights, dict)
        assert weights['user_engagement'] == 0.4
        assert weights['innovation'] == 0.3
    
    def test_get_weights_with_invalid_type(self, temp_config_file):
        """잘못된 프로젝트 유형으로 가중치 조회 테스트"""
        manager = WeightManager(temp_config_file)
        
        # 기본 유형(balanced)의 가중치가 반환되어야 함
        weights = manager.get_weights('invalid_type')
        
        assert isinstance(weights, dict)
        assert weights['business_value'] == 0.2  # balanced 유형의 가중치
    
    def test_apply_weights(self, temp_config_file):
        """가중치 적용 테스트"""
        manager = WeightManager(temp_config_file)
        
        scores = {
            'business_value': 8.0,
            'technical_feasibility': 7.0,
            'cost_analysis': 6.0,
            'user_engagement': 9.0,
            'innovation': 8.5
        }
        
        weights = {
            'business_value': 0.3,
            'technical_feasibility': 0.3,
            'cost_analysis': 0.2,
            'user_engagement': 0.1,
            'innovation': 0.1
        }
        
        weighted_scores = manager.apply_weights(scores, weights)
        
        assert weighted_scores['business_value'] == 8.0 * 0.3
        assert weighted_scores['technical_feasibility'] == 7.0 * 0.3
        assert weighted_scores['cost_analysis'] == 6.0 * 0.2
    
    def test_calculate_final_score(self, temp_config_file):
        """최종 점수 계산 테스트"""
        manager = WeightManager(temp_config_file)
        
        scores = {
            'business_value': 8.0,
            'technical_feasibility': 7.0,
            'cost_analysis': 6.0,
            'user_engagement': 9.0,
            'innovation': 8.5
        }
        
        final_score = manager.calculate_final_score(scores, 'painkiller')
        
        # 수동 계산: 8.0*0.3 + 7.0*0.3 + 6.0*0.2 + 9.0*0.1 + 8.5*0.1
        expected = 8.0*0.3 + 7.0*0.3 + 6.0*0.2 + 9.0*0.1 + 8.5*0.1
        assert abs(final_score - expected) < 0.001
    
    def test_weight_normalization(self):
        """가중치 정규화 테스트"""
        # 합계가 1.0이 아닌 가중치 설정
        config = {
            'weights': {
                'test_type': {
                    'chain1': 0.6,
                    'chain2': 0.6,  # 합계 1.2
                }
            },
            'default_settings': {
                'weight_sum_tolerance': 0.01,
                'log_normalization': True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f, default_flow_style=False)
            temp_path = f.name
        
        try:
            manager = WeightManager(temp_path)
            weights = manager.get_weights('test_type')
            
            # 정규화된 가중치 확인
            assert abs(weights['chain1'] - 0.5) < 0.001  # 0.6/1.2 = 0.5
            assert abs(weights['chain2'] - 0.5) < 0.001  # 0.6/1.2 = 0.5
            assert abs(sum(weights.values()) - 1.0) < 0.001
            
        finally:
            os.unlink(temp_path)
    
    def test_negative_weight_validation(self):
        """음수 가중치 검증 테스트"""
        config = {
            'weights': {
                'test_type': {
                    'chain1': 0.8,
                    'chain2': -0.2,  # 음수 가중치
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f, default_flow_style=False)
            temp_path = f.name
        
        try:
            # ValueError가 발생해야 함
            with pytest.raises(ValueError, match="음수 가중치는 허용되지 않습니다"):
                WeightManager(temp_path)
                
        finally:
            os.unlink(temp_path)
    
    def test_get_available_project_types(self, temp_config_file):
        """사용 가능한 프로젝트 유형 목록 조회 테스트"""
        manager = WeightManager(temp_config_file)
        
        types = manager.get_available_project_types()
        
        assert 'painkiller' in types
        assert 'vitamin' in types
        assert 'balanced' in types
        assert len(types) == 3
    
    def test_get_weight_summary(self, temp_config_file):
        """가중치 요약 정보 조회 테스트"""
        manager = WeightManager(temp_config_file)
        
        summary = manager.get_weight_summary('painkiller')
        
        assert 'painkiller 유형 가중치' in summary
        assert 'business_value' in summary
        assert '30.0%' in summary  # 0.3 * 100
    
    def test_reload_config(self, temp_config_file):
        """설정 파일 재로드 테스트"""
        manager = WeightManager(temp_config_file)
        
        # 초기 가중치 확인
        initial_weight = manager.get_weights('painkiller')['business_value']
        
        # 설정 파일 수정
        new_config = {
            'weights': {
                'painkiller': {
                    'business_value': 0.5,  # 변경된 값
                    'technical_feasibility': 0.5
                }
            },
            'default_settings': {}
        }
        
        with open(temp_config_file, 'w') as f:
            yaml.dump(new_config, f)
        
        # 재로드
        manager.reload_config()
        
        # 변경된 가중치 확인
        updated_weight = manager.get_weights('painkiller')['business_value']
        assert updated_weight != initial_weight
        assert updated_weight == 0.5
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_file_not_found_fallback(self, mock_file):
        """파일을 찾을 수 없을 때 기본 가중치 사용 테스트"""
        manager = WeightManager('/nonexistent/path.yaml')
        
        # 기본 가중치가 로드되어야 함
        weights = manager.get_weights('balanced')
        assert isinstance(weights, dict)
        assert len(weights) > 0
    
    def test_empty_config_file(self):
        """빈 설정 파일 처리 테스트"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write('')  # 빈 파일
            temp_path = f.name
        
        try:
            manager = WeightManager(temp_path)
            
            # 기본 가중치가 로드되어야 함
            weights = manager.get_weights('balanced')
            assert isinstance(weights, dict)
            assert len(weights) > 0
            
        finally:
            os.unlink(temp_path)
    
    def test_auto_reload_disabled(self, temp_config_file):
        """자동 재로드 비활성화 테스트"""
        manager = WeightManager(temp_config_file, auto_reload=False)
        
        # 파일 감시 스레드가 시작되지 않아야 함
        assert manager._file_watcher_thread is None
        assert manager.auto_reload is False
    
    def test_auto_reload_enabled(self, temp_config_file):
        """자동 재로드 활성화 테스트"""
        manager = WeightManager(temp_config_file, auto_reload=True)
        
        try:
            # 파일 감시 스레드가 시작되어야 함
            assert manager._file_watcher_thread is not None
            assert manager.auto_reload is True
            
            # 스레드가 실행 중이어야 함
            import time
            time.sleep(0.1)  # 스레드 시작 대기
            assert manager._file_watcher_thread.is_alive()
            
        finally:
            manager.stop_file_watcher()
    
    def test_file_watcher_stop(self, temp_config_file):
        """파일 감시 스레드 중지 테스트"""
        manager = WeightManager(temp_config_file, auto_reload=True)
        
        # 스레드가 시작되었는지 확인
        assert manager._file_watcher_thread is not None
        
        # 스레드 중지
        manager.stop_file_watcher()
        
        # 스레드가 중지되었는지 확인
        assert manager._file_watcher_thread is None
        assert manager._stop_watcher.is_set()
    
    def test_auto_file_reload(self, temp_config_file):
        """파일 변경 시 자동 재로드 테스트"""
        manager = WeightManager(temp_config_file, auto_reload=True)
        
        try:
            # 초기 가중치 확인
            initial_weight = manager.get_weights('painkiller')['business_value']
            
            # 파일 수정 (약간의 지연 후)
            import time
            time.sleep(0.1)
            new_config = {
                'weights': {
                    'painkiller': {
                        'business_value': 0.9,  # 변경된 값
                        'technical_feasibility': 0.1
                    }
                },
                'default_settings': {}
            }
            
            with open(temp_config_file, 'w') as f:
                yaml.dump(new_config, f)
            
            # 자동 재로드 대기 (최대 3초)
            for _ in range(30):
                time.sleep(0.1)
                current_weight = manager.get_weights('painkiller')['business_value']
                if current_weight != initial_weight:
                    break
            
            # 변경된 가중치 확인
            updated_weight = manager.get_weights('painkiller')['business_value']
            assert updated_weight != initial_weight
            assert updated_weight == 0.9
            
        finally:
            manager.stop_file_watcher()