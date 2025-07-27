# -*- coding: utf-8 -*-
"""
pytest 설정 파일
"""

import pytest
import sys
import os
import logging

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def test_s3_uri():
    """테스트용 S3 URI"""
    return "https://s3.us-east-1.amazonaws.com/victor.kim-temporary/hackathon/carenity.pdf"


@pytest.fixture(scope="session")
def sample_project_data():
    """테스트용 프로젝트 데이터"""
    return {
        "simple": "AI 기반 모바일 앱",
        "detailed": """
프로젝트명: AI 기반 헬스케어 모니터링 시스템

프로젝트 설명:
- 웨어러블 디바이스와 연동하여 실시간 건강 데이터 수집
- AI 알고리즘으로 이상 징후 조기 발견 및 알림
- 의료진과의 원격 상담 플랫폼 제공

타겟 고객:
- 만성질환자 (당뇨, 고혈압 등)
- 고령자 및 그 가족

비즈니스 모델:
- 월 구독료 (개인: 월 3만원, 가족: 월 8만원)
- 의료기관 B2B 라이선스
""",
        "pain_killer": """
응급실 대기시간 단축 시스템
- 생명과 직결된 응급 상황 해결
- 의료진 업무 효율성 극대화
- 환자 안전성 향상
""",
        "vitamin": """
소셜 미디어 사진 필터 앱
- 재미있는 사진 편집 기능
- 소셜 공유 기능
- 사용자 경험 향상
"""
    }


@pytest.fixture
def empty_analysis_input():
    """빈 분석 입력 데이터"""
    return {
        "video_analysis": {"s3_uri": ""},
        "document_analysis": {"s3_uri": ""},
        "presentation_analysis": {"s3_uri": ""}
    }


@pytest.fixture
def mixed_analysis_input(test_s3_uri):
    """혼합 분석 입력 데이터 (일부는 유효, 일부는 빈 값)"""
    return {
        "video_analysis": {"s3_uri": ""},
        "document_analysis": {"s3_uri": ""},
        "presentation_analysis": {"s3_uri": test_s3_uri}
    }


@pytest.fixture
def main_py_user_input(test_s3_uri):
    """main.py와 동일한 사용자 입력 형식"""
    return {
        "video_uri": "",
        "document_uri": "",
        "presentation_uri": test_s3_uri
    }


# 테스트 실행 시 출력 설정
def pytest_configure(config):
    """pytest 설정"""
    # 실시간 출력 활성화
    config.option.capture = "no"
    config.option.verbose = True
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True  # 기존 설정 덮어쓰기
    )
    
    # 테스트 로거 레벨 명시적 설정
    test_logger = logging.getLogger('tests.test_analysis_modules')
    test_logger.setLevel(logging.INFO)


# 테스트 결과 요약
def pytest_sessionfinish(session, exitstatus):
    """테스트 세션 종료 시 실행"""
    if exitstatus == 0:
        print("\n🎉 모든 테스트가 성공적으로 완료되었습니다!")
    else:
        print(f"\n⚠️ 일부 테스트가 실패했습니다. (종료 코드: {exitstatus})")


# 느린 테스트 마킹
def pytest_collection_modifyitems(config, items):
    """테스트 수집 후 수정"""
    for item in items:
        # 통합 테스트나 LLM 호출이 포함된 테스트는 slow 마크 추가
        if "integration" in item.nodeid or "llm" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)


# 커스텀 마커 정의
def pytest_configure(config):
    """커스텀 마커 등록"""
    config.addinivalue_line(
        "markers", "slow: 실행 시간이 오래 걸리는 테스트"
    )
    config.addinivalue_line(
        "markers", "integration: 통합 테스트"
    )
    config.addinivalue_line(
        "markers", "unit: 단위 테스트"
    )