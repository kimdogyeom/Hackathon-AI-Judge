#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹 애플리케이션 실행 스크립트
"""
import sys
import os
import subprocess
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """웹 애플리케이션 실행"""
    try:
        # Streamlit 앱 실행
        app_path = project_root / "src" / "web" / "app.py"
        
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            str(app_path),
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false"
        ]
        
        print("🚀 프로젝트 평가 시스템 웹 서버를 시작합니다...")
        print(f"📍 URL: http://localhost:8501")
        print("⏹️  종료하려면 Ctrl+C를 누르세요")
        print("-" * 50)
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 웹 서버가 종료되었습니다.")
    except Exception as e:
        print(f"❌ 웹 서버 실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()