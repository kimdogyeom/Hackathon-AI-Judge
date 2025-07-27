# 테스트 가이드

이 디렉토리는 프로젝트 유형 평가 시스템의 테스트를 포함합니다.

## 테스트 구조

```
tests/
├── conftest.py                 # pytest 설정 및 공통 픽스처
├── unit/                       # 단위 테스트
│   ├── analysis/              # 분석 모듈 테스트
│   │   └── test_analysis_modules.py
│   ├── chain/                 # 평가 체인 테스트
│   │   ├── test_accessibility_chain.py
│   │   ├── test_base_evaluation_chain.py
│   │   ├── test_business_value_chain.py
│   │   ├── test_cost_analysis_chain.py
│   │   ├── test_innovation_chain.py
│   │   ├── test_network_effect_chain.py
│   │   ├── test_social_impact_chain.py
│   │   ├── test_sustainability_chain.py
│   │   ├── test_technical_feasibility_chain.py
│   │   └── test_user_engagement_chain.py
│   ├── classifier/            # 분류기 테스트
│   │   └── test_project_type_classifier.py
│   └── config/                # 설정 관리 테스트
│       ├── test_config_manager.py
│       └── test_weight_manager.py
├── integration/               # 통합 테스트
│   ├── test_integration.py    # 기본 통합 테스트
│   └── test_real_data_integration.py  # 실제 데이터 통합 테스트
└── e2e/                      # End-to-End 테스트 (향후 확장)
```

## 테스트 유형별 설명

### 단위 테스트 (Unit Tests)
개별 컴포넌트의 기능을 독립적으로 테스트합니다.

- **analysis/**: 비디오, 문서, 발표자료 분석 모듈 테스트
- **chain/**: 각 평가 체인의 개별 기능 테스트
- **classifier/**: 프로젝트 유형 분류기 테스트
- **config/**: 설정 관리 및 가중치 관리 테스트

### 통합 테스트 (Integration Tests)
여러 컴포넌트 간의 상호작용을 테스트합니다.

- **test_integration.py**: 전체 파이프라인 통합 테스트
- **test_real_data_integration.py**: 실제 프로젝트 데이터를 사용한 테스트

### End-to-End 테스트 (E2E Tests)
전체 시스템의 완전한 플로우를 테스트합니다. (향후 확장 예정)

## 실행 방법

### 전체 테스트 실행
```bash
# 모든 테스트 실행
pytest tests/

# 상세 출력으로 실행
pytest tests/ -v
```

### 테스트 유형별 실행
```bash
# 단위 테스트만 실행
pytest tests/unit/ -v

# 통합 테스트만 실행
pytest tests/integration/ -v

# 특정 모듈 테스트 실행
pytest tests/unit/chain/ -v
pytest tests/unit/analysis/ -v
```

### 특정 테스트 파일 실행
```bash
# 특정 테스트 파일 실행
pytest tests/unit/chain/test_business_value_chain.py -v

# 특정 테스트 클래스 실행
pytest tests/integration/test_integration.py::TestEndToEndPipeline -v

# 특정 테스트 메서드 실행
pytest tests/integration/test_integration.py::TestEndToEndPipeline::test_complete_pipeline_with_painkiller_project -v
```

### 마커별 실행
```bash
# 빠른 테스트만 실행 (slow 마커 제외)
pytest tests/ -m "not slow" -v

# 통합 테스트만 실행
pytest tests/ -m "integration" -v

# 단위 테스트만 실행
pytest tests/ -m "unit" -v
```

## 테스트 마커

- `slow`: 실행 시간이 오래 걸리는 테스트 (LLM 호출 포함)
- `integration`: 통합 테스트
- `unit`: 단위 테스트

## 테스트 작성 가이드

### 단위 테스트 작성
```python
import pytest
from src.chain.business_value_chain import BusinessValueChain

class TestBusinessValueChain:
    def test_basic_functionality(self):
        chain = BusinessValueChain()
        result = chain.invoke(test_input)
        assert result is not None
```

### 통합 테스트 작성
```python
import pytest

class TestPipelineIntegration:
    @pytest.mark.integration
    def test_full_pipeline(self):
        # 전체 파이프라인 테스트
        pass
```

### 픽스처 사용
```python
def test_with_fixture(self, sample_project_data):
    # conftest.py에 정의된 픽스처 사용
    assert sample_project_data is not None
```

## 주요 테스트 시나리오

### 단위 테스트 시나리오
1. **분석 모듈**: 빈 URI, 유효한 URI, 오류 처리
2. **평가 체인**: 각 체인의 개별 기능, 점수 계산, 오류 처리
3. **분류기**: 프로젝트 유형 분류, 신뢰도 계산
4. **설정 관리**: 가중치 로드, 설정 검증

### 통합 테스트 시나리오
1. **전체 파이프라인**: 분석 → 분류 → 평가 → 가중치 적용
2. **프로젝트 유형별**: PainKiller, Vitamin, Balanced 각각의 플로우
3. **오류 처리**: 빈 데이터, 체인 실패, 네트워크 오류
4. **성능 테스트**: 실행 시간, 일관성, 메모리 사용량

## 성능 기준

### 응답 시간
- **단위 테스트**: 평균 5초 이내
- **통합 테스트**: 평균 35초 이내
- **전체 파이프라인**: 60초 이내

### 정확성
- **점수 범위**: 0-10 사이
- **가중치 합계**: 1.0
- **일관성**: 동일 입력에 대해 일관된 결과

## 문제 해결

### 테스트 실패 시
1. 오류 메시지 확인
2. AWS 자격 증명 확인
3. S3 URI 접근 가능성 확인
4. 네트워크 연결 상태 확인

### 느린 테스트
```bash
# 빠른 테스트만 실행
pytest tests/ -m "not slow"
```

### 디버깅
```bash
# 상세한 출력과 함께 실행
pytest tests/ -v -s --tb=long
```

## 기여 가이드

### 새로운 테스트 추가 시
1. 적절한 디렉토리에 테스트 파일 추가
2. 명확한 테스트 이름 사용
3. 필요한 경우 fixture 활용
4. 적절한 마커 추가

### 테스트 작성 원칙
1. **독립성**: 각 테스트는 독립적으로 실행 가능해야 함
2. **반복성**: 동일한 결과를 보장해야 함
3. **명확성**: 테스트 목적이 명확해야 함
4. **완전성**: 정상 및 오류 시나리오 모두 포함

## 참고사항

- 모든 테스트는 실제 AWS Bedrock Nova Lite 모델을 호출합니다
- 네트워크 연결과 AWS 자격 증명이 필요합니다
- 일부 테스트는 실행 시간이 오래 걸릴 수 있습니다
- 테스트 실행 전 `pip install pytest` 필요