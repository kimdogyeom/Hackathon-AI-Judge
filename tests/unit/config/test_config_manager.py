"""
설정 관리자 테스트 모듈
"""

import pytest
import tempfile
import yaml
import time
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.config.config_manager import ConfigManager, get_config_manager


class TestConfigManager:
    """설정 관리자 테스트 클래스"""
    
    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)
        
    def teardown_method(self):
        """각 테스트 메서드 실행 후 정리"""
        # 임시 파일들 정리
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_config_file(self, filename: str, content: dict):
        """테스트용 설정 파일 생성"""
        file_path = self.config_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(content, f, allow_unicode=True)
        return file_path
    
    def test_config_manager_initialization(self):
        """설정 관리자 초기화 테스트"""
        config_manager = ConfigManager(self.config_dir)
        
        # 기본 설정이 로드되었는지 확인
        assert 'chain_weights.yaml' in config_manager._configs
        assert 'project_classification.yaml' in config_manager._configs
        
        # 파일 감시가 시작되었는지 확인
        assert hasattr(config_manager, 'observer')
        assert config_manager.observer.is_alive()
        
        config_manager.stop_watching()
    
    def test_load_valid_config_file(self):
        """유효한 설정 파일 로드 테스트"""
        # 테스트용 가중치 설정 파일 생성
        test_weights = {
            'weights': {
                'painkiller': {
                    'business_value': 0.3,
                    'technical_feasibility': 0.2,
                    'cost_analysis': 0.2,
                    'user_engagement': 0.1,
                    'innovation': 0.1,
                    'social_impact': 0.05,
                    'sustainability': 0.03,
                    'accessibility': 0.01,
                    'network_effect': 0.01
                }
            }
        }
        
        self.create_test_config_file('chain_weights.yaml', test_weights)
        
        config_manager = ConfigManager(self.config_dir)
        
        # 설정이 올바르게 로드되었는지 확인
        loaded_weights = config_manager.get_config('chain_weights.yaml', 'weights.painkiller')
        assert loaded_weights['business_value'] == 0.3
        assert loaded_weights['technical_feasibility'] == 0.2
        
        config_manager.stop_watching()
    
    def test_invalid_yaml_file_handling(self):
        """잘못된 YAML 파일 처리 테스트"""
        # 잘못된 YAML 파일 생성
        file_path = self.config_dir / 'chain_weights.yaml'
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("invalid: yaml: content: [")
        
        with patch('src.config.config_manager.logger') as mock_logger:
            config_manager = ConfigManager(self.config_dir)
            
            # 오류 로그가 기록되었는지 확인
            mock_logger.error.assert_called()
            
            # 기본값이 사용되었는지 확인
            weights = config_manager.get_weights('painkiller')
            assert 'business_value' in weights
            assert weights['business_value'] == 0.25  # 기본값
        
        config_manager.stop_watching()
    
    def test_weight_normalization(self):
        """가중치 정규화 테스트"""
        # 합계가 1.0이 아닌 가중치 설정
        test_weights = {
            'weights': {
                'painkiller': {
                    'business_value': 0.5,  # 합계가 1.0을 초과
                    'technical_feasibility': 0.4,
                    'cost_analysis': 0.3,
                    'user_engagement': 0.2,
                    'innovation': 0.1,
                    'social_impact': 0.1,
                    'sustainability': 0.1,
                    'accessibility': 0.1,
                    'network_effect': 0.1
                }
            }
        }
        
        self.create_test_config_file('chain_weights.yaml', test_weights)
        
        with patch('src.config.config_manager.logger') as mock_logger:
            config_manager = ConfigManager(self.config_dir)
            
            # 정규화 경고가 기록되었는지 확인
            mock_logger.warning.assert_called()
            
            # 가중치가 정규화되었는지 확인
            weights = config_manager.get_weights('painkiller')
            weight_sum = sum(weights.values())
            assert abs(weight_sum - 1.0) < 0.001  # 정규화 후 합계가 1.0에 가까워야 함
        
        config_manager.stop_watching()
    
    def test_missing_config_file_handling(self):
        """설정 파일이 없는 경우 처리 테스트"""
        # 빈 디렉토리에서 설정 관리자 생성
        with patch('src.config.config_manager.logger') as mock_logger:
            config_manager = ConfigManager(self.config_dir)
            
            # 경고 로그가 기록되었는지 확인
            mock_logger.warning.assert_called()
            
            # 기본값이 사용되었는지 확인
            weights = config_manager.get_weights('painkiller')
            assert 'business_value' in weights
            assert weights['business_value'] == 0.25  # 기본값
        
        config_manager.stop_watching()
    
    def test_invalid_confidence_threshold(self):
        """잘못된 신뢰도 임계값 처리 테스트"""
        test_classification = {
            'classification': {
                'confidence_threshold': 1.5,  # 잘못된 값 (0-1 범위 초과)
                'painkiller_keywords': ['test'],
                'vitamin_keywords': ['test']
            }
        }
        
        self.create_test_config_file('project_classification.yaml', test_classification)
        
        with patch('src.config.config_manager.logger') as mock_logger:
            config_manager = ConfigManager(self.config_dir)
            
            # 경고 로그가 기록되었는지 확인
            mock_logger.warning.assert_called()
            
            # 기본값이 사용되었는지 확인
            classification_config = config_manager.get_classification_config()
            assert classification_config['confidence_threshold'] == 0.7  # 기본값
        
        config_manager.stop_watching()
    
    def test_get_config_with_key_path(self):
        """키 경로를 사용한 설정 조회 테스트"""
        test_config = {
            'level1': {
                'level2': {
                    'level3': 'test_value'
                }
            }
        }
        
        self.create_test_config_file('test_config.yaml', test_config)
        
        config_manager = ConfigManager(self.config_dir)
        
        # 키 경로를 사용한 조회
        value = config_manager.get_config('test_config.yaml', 'level1.level2.level3')
        assert value == 'test_value'
        
        # 존재하지 않는 키 경로 조회
        value = config_manager.get_config('test_config.yaml', 'nonexistent.key')
        assert value is None
        
        config_manager.stop_watching()
    
    @pytest.mark.skipif(True, reason="파일 감시 테스트는 시간이 오래 걸리므로 필요시에만 실행")
    def test_file_watching_and_reload(self):
        """파일 감시 및 재로드 테스트"""
        # 초기 설정 파일 생성
        initial_weights = {
            'weights': {
                'painkiller': {
                    'business_value': 0.3,
                    'technical_feasibility': 0.7
                }
            }
        }
        
        config_file = self.create_test_config_file('chain_weights.yaml', initial_weights)
        
        config_manager = ConfigManager(self.config_dir)
        
        # 초기값 확인
        initial_value = config_manager.get_config('chain_weights.yaml', 'weights.painkiller.business_value')
        assert initial_value == 0.3
        
        # 파일 수정
        modified_weights = {
            'weights': {
                'painkiller': {
                    'business_value': 0.5,
                    'technical_feasibility': 0.5
                }
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(modified_weights, f, allow_unicode=True)
        
        # 파일 변경 감지 대기
        time.sleep(1)
        
        # 변경된 값 확인
        modified_value = config_manager.get_config('chain_weights.yaml', 'weights.painkiller.business_value')
        assert modified_value == 0.5
        
        config_manager.stop_watching()
    
    def test_singleton_pattern(self):
        """싱글톤 패턴 테스트"""
        # 전역 설정 관리자 인스턴스 초기화
        import src.config.config_manager
        src.config.config_manager._config_manager = None
        
        # 두 번 호출해도 같은 인스턴스 반환
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        assert manager1 is manager2
        
        manager1.stop_watching()
    
    def test_thread_safety(self):
        """스레드 안전성 테스트"""
        config_manager = ConfigManager(self.config_dir)
        results = []
        
        def get_config_worker():
            """설정 조회 작업자 함수"""
            for _ in range(100):
                weights = config_manager.get_weights('painkiller')
                results.append(weights['business_value'])
        
        # 여러 스레드에서 동시에 설정 조회
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=get_config_worker)
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        # 모든 결과가 일관되는지 확인
        assert len(results) == 500
        assert all(result == 0.25 for result in results)  # 기본값
        
        config_manager.stop_watching()


class TestConfigManagerIntegration:
    """설정 관리자 통합 테스트"""
    
    def test_integration_with_weight_manager(self):
        """가중치 관리자와의 통합 테스트"""
        from src.config.config import get_config_manager
        
        config_manager = get_config_manager()
        
        # 가중치 조회가 정상 작동하는지 확인
        weights = config_manager.get_weights('painkiller')
        assert isinstance(weights, dict)
        assert 'business_value' in weights
        assert isinstance(weights['business_value'], (int, float))
        
        config_manager.stop_watching()
    
    def test_integration_with_classification_config(self):
        """분류 설정과의 통합 테스트"""
        from src.config.config import get_config_manager
        
        config_manager = get_config_manager()
        
        # 분류 설정 조회가 정상 작동하는지 확인
        classification_config = config_manager.get_classification_config()
        assert isinstance(classification_config, dict)
        assert 'confidence_threshold' in classification_config
        assert 'painkiller_keywords' in classification_config
        assert 'vitamin_keywords' in classification_config
        
        config_manager.stop_watching()