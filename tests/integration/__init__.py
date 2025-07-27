# -*- coding: utf-8 -*-
"""
통합 테스트 모듈
여러 컴포넌트 간의 상호작용을 테스트합니다.
"""

import pytest

# 이 디렉토리의 모든 테스트에 integration 마커 적용
pytestmark = pytest.mark.integration