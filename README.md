# 해커톤 AI 심사 시스템

## 📖 개요

해커톤 AI 심사 시스템은 AWS Bedrock 기반의 LLM(Claude Sonnet, Nova Pro/Lite)을 활용하여 해커톤 출품작을 다각적으로 평가하는 자동화 시스템입니다. 문서, 발표자료, 시연 영상 등 다양한 형식의 프로젝트 자료를 분석하여 비즈니스 가치, 기술적 실현 가능성, 혁신성 등 9가지 항목에 대해 정량적/정성적 평가를 수행합니다.

본 시스템은 Streamlit 기반의 웹 인터페이스를 통해 사용자 친화적인 경험을 제공하며, 평가 결과는 시각화된 대시보드를 통해 직관적으로 확인할 수 있습니다.

## ✨ 주요 기능

- **다중 LLM 지원**: AWS Bedrock의 Claude Sonnet, Nova Pro/Lite 등 다양한 LLM을 활용하여 평가의 유연성과 확장성을 확보했습니다.
- **종합적인 평가 체계**: 9가지 평가 항목(비즈니스 가치, 기술적 실현 가능성, 혁신성 등)에 대한 개별 점수 및 종합 점수를 제공합니다.
- **프로젝트 유형 분류**: AI가 프로젝트의 특성을 'Painkiller'와 'Vitamin'으로 자동 분류하여 맞춤형 가중치를 적용합니다.
- **다양한 파일 형식 지원**: 프로젝트 설명 문서(TXT, DOC, DOCX), 발표자료(PDF, 이미지), 시연 영상(MP4) 등 다양한 형식의 파일을 분석합니다.
- **S3 기반 파일 처리**: 대용량 파일(특히, 동영상)의 안정적인 처리를 위해 AWS S3와 연동하여 파일을 업로드하고 분석합니다.
- **사용자 친화적 대시보드**: Streamlit을 사용하여 구현된 웹 인터페이스를 통해 파일 업로드, 분석 진행 상황 확인, 시각화된 평가 결과를 손쉽게 확인할 수 있습니다.
- **결과 공유 기능**: 분석 결과를 고유 링크로 생성하여 다른 사람과 공유할 수 있습니다.

## 🛠️ 기술 스택

### Backend

- **Python 3.12**
- **AI/LLM Frameworks**: LangChain, LangSmith
- **LLM**: AWS Bedrock (Claude Sonnet, Nova Pro/Lite)
- **Web Framework**: Streamlit
- **Data Handling**: Pandas, NumPy
- **AWS Integration**: Boto3
- **Configuration**: Pydantic, python-dotenv

### Frontend

- **Streamlit**
- **Visualization**: Plotly

### Testing

- **Pytest**

## ⚙️ 설치 및 실행

### 1. 저장소 복제

```bash
git clone https://github.com/your-username/hackathon_judge.git
cd hackathon_judge
```

### 2. 가상환경 생성 및 활성화

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env` 파일을 생성하고 아래와 같이 AWS 자격 증명 및 기타 설정을 추가합니다.

```env
# AWS Credentials
AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY"
AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_KEY"
AWS_REGION_NAME="us-east-1"

# S3 Bucket
S3_BUCKET_NAME="your-s3-bucket-name"

# LangSmith (Optional)
LANGCHAIN_TRACING_V2="true"
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="YOUR_LANGCHAIN_API_KEY"
LANGCHAIN_PROJECT="hackathon_judge"
```

### 5. 웹 애플리케이션 실행

```bash
streamlit run src/web/app.py
```

### 6. 테스트 실행 (선택 사항)

```bash
pytest
```

## 📂 프로젝트 구조

```
/hackathon_judge
├── src/
│   ├── analysis/       # 파일(문서, 영상 등) 분석 모듈
│   ├── chain/          # LangChain 기반 평가 체인
│   ├── classifier/     # 프로젝트 유형 분류기
│   ├── config/         # 설정 관리
│   ├── llm/            # LLM 모델 래퍼
│   ├── uploads/        # 파일 업로드 및 S3 연동
│   └── web/            # Streamlit 웹 애플리케이션
├── tests/              # 단위, 통합, E2E 테스트
├── .env                # 환경 변수 파일
├── requirements.txt    # Python 의존성 목록
├── README.md           # 프로젝트 소개
└── ...
```

