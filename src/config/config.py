import os
import yaml
from pathlib import Path

import dotenv
dotenv.load_dotenv(override=True)

RESOURCE_BUCKET_NAME = os.getenv('resource_bucket_name')

import boto3

s3_client = boto3.client('s3')

# 파일 업로드 관련 설정
ALLOWED_EXTENSIONS = {
    "video": ["mp4", "mov", "avi", "wmv"],
    "document": ["pdf", "docx", "txt", "md"],
    "presentation": ["pptx", "ppt", "key"]
}
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 100 * 1024 * 1024))  # 기본 100MB



# 평가 체인 가중치 설정 (레거시 지원)
CHAIN_WEIGHTS = {
    "business_value": float(os.getenv("WEIGHT_BUSINESS_VALUE", 1.0)),
    "technical_feasibility": float(os.getenv("WEIGHT_TECHNICAL_FEASIBILITY", 1.0)),
    "user_engagement": float(os.getenv("WEIGHT_USER_ENGAGEMENT", 1.0)),
    "innovation": float(os.getenv("WEIGHT_INNOVATION", 1.0)),
    "cost_analysis": float(os.getenv("WEIGHT_COST_ANALYSIS", 1.0)),
    "accessibility": float(os.getenv("WEIGHT_ACCESSIBILITY", 1.0)),
    "social_impact": float(os.getenv("WEIGHT_SOCIAL_IMPACT", 1.0)),
    "sustainability": float(os.getenv("WEIGHT_SUSTAINABILITY", 1.0)),
    "network_effect": float(os.getenv("WEIGHT_NETWORK_EFFECT", 1.0)),
}

# 가중치 관리자 인스턴스 (프로젝트 유형별 가중치 지원)
_weight_manager = None

def get_weight_manager():
    """가중치 관리자 인스턴스 반환 (싱글톤 패턴)"""
    global _weight_manager
    if _weight_manager is None:
        from .weight_manager import WeightManager
        _weight_manager = WeightManager()
    return _weight_manager

# 설정 관리자 인스턴스
_config_manager = None

def get_config_manager():
    """설정 관리자 인스턴스 반환 (싱글톤 패턴)"""
    global _config_manager
    if _config_manager is None:
        from .config_manager import ConfigManager
        _config_manager = ConfigManager()
    return _config_manager

def get_chain_weights(project_type: str = None):
    """
    평가 체인 가중치 반환
    
    Args:
        project_type: 프로젝트 유형 ("painkiller", "vitamin", "balanced")
                     None인 경우 레거시 CHAIN_WEIGHTS 반환
    
    Returns:
        Dict[str, float]: 평가 체인별 가중치
    """
    if project_type is None:
        # 레거시 지원: 환경변수 기반 가중치
        return CHAIN_WEIGHTS.copy()
    else:
        # 새로운 방식: 프로젝트 유형별 가중치
        weight_manager = get_weight_manager()
        return weight_manager.get_weights(project_type)

# 시스템 프롬프트 로드 함수
def load_system_prompts():
    """시스템 프롬프트 YAML 파일을 로드합니다."""
    config_dir = Path(__file__).parent
    prompts_file = config_dir / "system_prompts.yaml"
    
    try:
        with open(prompts_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"시스템 프롬프트 파일을 찾을 수 없습니다: {prompts_file}")
    except yaml.YAMLError as e:
        raise ValueError(f"YAML 파일 파싱 오류: {e}")

# 시스템 프롬프트 캐시
_system_prompts_cache = None

def get_system_prompt(analysis_type):
    """
    특정 분석 타입의 시스템 프롬프트를 반환합니다.
    
    Args:
        analysis_type (str): 'video_analysis', 'document_analysis', 'presentation_analysis'
    
    Returns:
        str: 시스템 프롬프트 텍스트
    """
    global _system_prompts_cache
    
    if _system_prompts_cache is None:
        _system_prompts_cache = load_system_prompts()
    
    if analysis_type not in _system_prompts_cache:
        raise ValueError(f"지원하지 않는 분석 타입: {analysis_type}")
    
    prompt_config = _system_prompts_cache[analysis_type]
    system_prompt = prompt_config.get('system_prompt', '')
    
    # 공통 지침 추가
    common_guidelines = _system_prompts_cache.get('common_guidelines', '')
    if common_guidelines:
        system_prompt += f"\n\n## 공통 지침\n{common_guidelines}"
    
    # 출력 형식 추가
    output_format = _system_prompts_cache.get('output_format', {}).get('structure', '')
    if output_format:
        system_prompt += f"\n\n## 출력 형식\n{output_format}"
    
    return system_prompt

# S3 스토리지 객체 반환 함수
def get_storage():
    """S3 스토리지 객체 반환"""
    from src.uploads.s3_storage import S3Storage
    return S3Storage(
        bucket_name=RESOURCE_BUCKET_NAME,
        s3_client=s3_client
    )

# 파일 업로더 객체 반환 함수
def get_file_uploader():
    """파일 업로더 객체 반환"""
    from src.uploads.file_uploader import FileUploader
    storage = get_storage()
    return FileUploader(storage=storage)


