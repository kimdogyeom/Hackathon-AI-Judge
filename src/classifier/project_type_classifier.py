# -*- coding: utf-8 -*-
import yaml
import re
from pathlib import Path
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ProjectTypeClassifier:
    """
    프로젝트 자료를 분석하여 PainKiller/Vitamin/Balanced 유형을 분류하는 클래스
    """
    
    def __init__(self, config_path: str = None):
        """
        분류기 초기화
        
        Args:
            config_path (str, optional): 설정 파일 경로. None이면 기본 경로 사용
        """
        if config_path is None:
            config_dir = Path(__file__).parent.parent / "config"
            config_path = config_dir / "project_classification.yaml"
        
        self.config = self._load_config(config_path)
        self.confidence_threshold = self.config["classification"]["confidence_threshold"]
        self.painkiller_keywords = self.config["classification"]["painkiller_keywords"]
        self.vitamin_keywords = self.config["classification"]["vitamin_keywords"]
        
    def _load_config(self, config_path: Path) -> Dict:
        """
        설정 파일을 로드합니다.
        
        Args:
            config_path (Path): 설정 파일 경로
            
        Returns:
            Dict: 설정 데이터
            
        Raises:
            FileNotFoundError: 설정 파일을 찾을 수 없는 경우
            ValueError: YAML 파싱 오류가 발생한 경우
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"프로젝트 분류 설정 파일을 찾을 수 없습니다: {config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"설정 파일 YAML 파싱 오류: {e}")
    
    def classify(self, analysis_data: Dict) -> Dict:
        """
        프로젝트 자료를 분석하여 유형을 분류합니다.
        
        Args:
            analysis_data (Dict): 분석된 프로젝트 데이터
                - video_analysis: 비디오 분석 결과
                - document_analysis: 문서 분석 결과  
                - presentation_analysis: 발표자료 분석 결과
                
        Returns:
            Dict: 분류 결과
                - project_type: "painkiller" | "vitamin" | "balanced"
                - confidence: 신뢰도 (0.0 - 1.0)
                - painkiller_score: PainKiller 점수 (0.0 - 1.0)
                - vitamin_score: Vitamin 점수 (0.0 - 1.0)
                - reasoning: 분류 근거
                - warning_message: 경고 메시지 (신뢰도 낮을 때만)
        """
        try:
            # 분석 데이터에서 텍스트 추출
            combined_text = self._extract_text_from_analysis(analysis_data)
            
            # 키워드 기반 점수 계산
            painkiller_score = self._calculate_keyword_score(combined_text, self.painkiller_keywords)
            vitamin_score = self._calculate_keyword_score(combined_text, self.vitamin_keywords)
            
            # 점수 정규화 (0-1 범위로)
            total_score = painkiller_score + vitamin_score
            if total_score > 0:
                painkiller_score = painkiller_score / total_score
                vitamin_score = vitamin_score / total_score
            else:
                # 키워드가 전혀 매칭되지 않은 경우
                painkiller_score = 0.5
                vitamin_score = 0.5
            
            # 신뢰도 계산 (점수 차이가 클수록 높은 신뢰도)
            confidence = abs(painkiller_score - vitamin_score)
            
            # 프로젝트 유형 결정
            if confidence >= self.confidence_threshold:
                if painkiller_score > vitamin_score:
                    project_type = "painkiller"
                    reasoning = f"비용 절감과 효율성 개선에 중점을 둔 문제 해결형 프로젝트 (PainKiller 점수: {painkiller_score:.2f})"
                else:
                    project_type = "vitamin"
                    reasoning = f"사용자 경험과 혁신에 중점을 둔 개선형 프로젝트 (Vitamin 점수: {vitamin_score:.2f})"
                warning_message = None
            else:
                project_type = "balanced"
                reasoning = f"PainKiller와 Vitamin 특성을 모두 가진 복합형 프로젝트 (신뢰도: {confidence:.2f})"
                warning_message = f"분류 신뢰도가 임계값({self.confidence_threshold})보다 낮아 Balanced로 분류되었습니다."
            
            result = {
                "project_type": project_type,
                "confidence": confidence,
                "painkiller_score": painkiller_score,
                "vitamin_score": vitamin_score,
                "reasoning": reasoning,
                "warning_message": warning_message
            }
            
            logger.info(f"프로젝트 유형 분류 완료: {project_type} (신뢰도: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"프로젝트 유형 분류 중 오류 발생: {e}")
            # 오류 발생 시 기본값 반환
            return {
                "project_type": "balanced",
                "confidence": 0.0,
                "painkiller_score": 0.5,
                "vitamin_score": 0.5,
                "reasoning": "분류 과정에서 오류가 발생하여 기본값으로 설정되었습니다.",
                "warning_message": f"분류 오류: {str(e)}"
            }
    
    def _extract_text_from_analysis(self, analysis_data: Dict) -> str:
        """
        분석 데이터에서 텍스트를 추출합니다.
        
        Args:
            analysis_data (Dict): 분석 데이터
            
        Returns:
            str: 추출된 텍스트
        """
        texts = []
        
        # 각 분석 결과에서 텍스트 추출
        for analysis_type in ["video_analysis", "document_analysis", "presentation_analysis"]:
            analysis_result = analysis_data.get(analysis_type, {})
            
            if isinstance(analysis_result, dict):
                # 다양한 필드에서 텍스트 추출 시도
                for field in ["content", "text", "summary", "description", "analysis"]:
                    if field in analysis_result and analysis_result[field]:
                        texts.append(str(analysis_result[field]))
                
                # 중첩된 딕셔너리에서도 텍스트 추출
                for key, value in analysis_result.items():
                    if isinstance(value, str) and len(value) > 10:  # 의미있는 길이의 텍스트만
                        texts.append(value)
            elif isinstance(analysis_result, str):
                texts.append(analysis_result)
        
        combined_text = " ".join(texts).lower()
        logger.debug(f"추출된 텍스트 길이: {len(combined_text)} 문자")
        return combined_text
    
    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """
        텍스트에서 키워드 매칭 점수를 계산합니다.
        
        Args:
            text (str): 분석할 텍스트
            keywords (List[str]): 키워드 리스트
            
        Returns:
            float: 키워드 매칭 점수
        """
        score = 0.0
        matched_keywords = []
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # 한국어와 영어 모두 지원하는 매칭 방식
            # 1. 정확한 문자열 매칭 (공백 포함)
            if keyword_lower in text:
                match_count = text.count(keyword_lower)
                match_count = min(match_count, 3)  # 최대 3회까지만 카운트
                keyword_score = match_count * 1.0
                score += keyword_score
                matched_keywords.append(keyword)
            else:
                # 2. 단어 경계를 고려한 영어 키워드 매칭 (영어 키워드용)
                if re.search(r'[a-zA-Z]', keyword_lower):  # 영어가 포함된 키워드
                    pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                    matches = re.findall(pattern, text)
                    if matches:
                        match_count = min(len(matches), 3)
                        keyword_score = match_count * 1.0
                        score += keyword_score
                        matched_keywords.append(keyword)
        
        logger.debug(f"매칭된 키워드: {matched_keywords}, 총 점수: {score}")
        return score
    
    def get_classification_info(self) -> Dict:
        """
        현재 분류 설정 정보를 반환합니다.
        
        Returns:
            Dict: 분류 설정 정보
        """
        return {
            "confidence_threshold": self.confidence_threshold,
            "painkiller_keywords_count": len(self.painkiller_keywords),
            "vitamin_keywords_count": len(self.vitamin_keywords),
            "painkiller_keywords": self.painkiller_keywords[:5],  # 처음 5개만 표시
            "vitamin_keywords": self.vitamin_keywords[:5]  # 처음 5개만 표시
        }