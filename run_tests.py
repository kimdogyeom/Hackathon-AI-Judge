#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테스트 실행 스크립트
다양한 테스트 시나리오를 쉽게 실행할 수 있도록 도와주는 스크립트입니다.
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd, description):
    """명령어 실행 및 결과 출력"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"실행 명령어: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="프로젝트 유형 평가 시스템 테스트 실행기")
    parser.add_argument(
        "test_type",
        choices=["all", "unit", "integration", "chain", "config", "classifier", "fast", "slow"],
        help="실행할 테스트 유형"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="상세한 출력"
    )
    parser.add_argument(
        "-s", "--capture",
        action="store_true",
        help="실시간 출력 표시"
    )
    parser.add_argument(
        "--tb",
        choices=["short", "long", "line", "no"],
        default="short",
        help="트레이스백 형식"
    )
    
    args = parser.parse_args()
    
    # 기본 pytest 옵션
    base_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        base_cmd.append("-v")
    
    if args.capture:
        base_cmd.append("-s")
    
    base_cmd.extend(["--tb", args.tb])
    
    # 테스트 유형별 실행
    success = True
    
    if args.test_type == "all":
        # 모든 테스트 실행
        cmd = base_cmd + ["tests/"]
        success = run_command(cmd, "전체 테스트 실행")
        
    elif args.test_type == "unit":
        # 단위 테스트만 실행 (분석 모듈 제외 - 설정 문제로 인해)
        cmd = base_cmd + ["tests/unit/chain/", "tests/unit/config/", "tests/unit/classifier/"]
        success = run_command(cmd, "단위 테스트 실행 (체인, 설정, 분류기)")
        
    elif args.test_type == "integration":
        # 통합 테스트만 실행
        cmd = base_cmd + ["tests/integration/", "-m", "integration"]
        success = run_command(cmd, "통합 테스트 실행")
        
    elif args.test_type == "chain":
        # 평가 체인 테스트만 실행
        cmd = base_cmd + ["tests/unit/chain/"]
        success = run_command(cmd, "평가 체인 테스트 실행")
        
    elif args.test_type == "config":
        # 설정 관리 테스트만 실행
        cmd = base_cmd + ["tests/unit/config/"]
        success = run_command(cmd, "설정 관리 테스트 실행")
        
    elif args.test_type == "classifier":
        # 분류기 테스트만 실행
        cmd = base_cmd + ["tests/unit/classifier/"]
        success = run_command(cmd, "분류기 테스트 실행")
        
    elif args.test_type == "fast":
        # 빠른 테스트만 실행 (slow 마커 제외)
        cmd = base_cmd + ["tests/", "-m", "not slow"]
        success = run_command(cmd, "빠른 테스트 실행 (slow 마커 제외)")
        
    elif args.test_type == "slow":
        # 느린 테스트만 실행
        cmd = base_cmd + ["tests/", "-m", "slow"]
        success = run_command(cmd, "느린 테스트 실행 (slow 마커만)")
    
    # 결과 출력
    print(f"\n{'='*60}")
    if success:
        print("✅ 테스트 실행 완료!")
    else:
        print("❌ 테스트 실행 중 오류 발생")
    print(f"{'='*60}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())