# -*- coding: utf-8 -*-
import json
import re
from typing import Dict, Any, List, Optional
from src.analysis.base_analysis import BaseAnalysis
from src.llm.nova_pro_llm import NovaProLLM, InvalidInputError, UnsupportedFileTypeError
from src.config.config_manager import get_system_prompt


class VideoAnalysisError(Exception):
    """동영상 분석 관련 오류"""
    pass


class VideoAnalysis(BaseAnalysis):
    """
    비디오 처리기.
    비디오 데이터를 분석하여 정보를 추출합니다.
    요구사항 2.1, 2.2, 2.3, 2.4를 만족하는 강화된 동영상 분석 기능을 제공합니다.
    """
    
    def __init__(self):
        self.llm = NovaProLLM()
        self.system_prompt = get_system_prompt('video_analysis')

    def process(self, s3_uri: str) -> Dict[str, Any]:
        """
        S3 URI에 있는 비디오를 처리하고 분석 결과를 반환합니다.
        요구사항 2.1: 동영상 URI 처리 및 의미있는 분석 결과 반환
        요구사항 2.2: 텍스트 추출, 주요 내용 요약, 키워드 추출
        요구사항 2.3: 동영상 파일 오류 처리 및 적절한 오류 메시지 반환
        요구사항 2.4: 분석 결과를 다른 분석과 동일한 형식으로 구조화

        :param s3_uri: 분석할 동영상 파일의 S3 URI
        :return: 구조화된 분석 결과
        """
        try:
            # 입력 URI 검증 및 전처리
            validated_uri = self._validate_and_preprocess_uri(s3_uri)
            
            # Nova Pro 모델 호출
            response = self.llm.invoke(
                s3_uri=validated_uri,
                system_message=self.system_prompt,
                user_message=self._get_analysis_instruction(),
                temperature=0.3,  # 일관된 분석을 위한 낮은 온도
                max_tokens=4000   # 충분한 토큰 수
            )

            # 분석 결과 구조화 및 검증
            structured_result = self._structure_analysis_result(response, validated_uri)
            
            return {
                "status": "completed",
                "data": structured_result,
                "analysis_type": "video_analysis",
                "metadata": {
                    "source_uri": validated_uri,
                    "processing_timestamp": self._get_current_timestamp(),
                    "model_used": "nova-pro-v1:0"
                }
            }
            
        except InvalidInputError as e:
            return self._create_error_response(
                "invalid_input", 
                f"입력 오류: {str(e)}", 
                s3_uri
            )
        except UnsupportedFileTypeError as e:
            return self._create_error_response(
                "unsupported_format", 
                f"지원하지 않는 파일 형식: {str(e)}", 
                s3_uri
            )
        except VideoAnalysisError as e:
            return self._create_error_response(
                "analysis_error", 
                f"분석 처리 오류: {str(e)}", 
                s3_uri
            )
        except Exception as e:
            return self._create_error_response(
                "system_error", 
                f"시스템 오류가 발생했습니다: {str(e)}", 
                s3_uri
            )

    def _validate_and_preprocess_uri(self, s3_uri: str) -> str:
        """
        URI 유효성 검증 및 전처리
        요구사항 2.1, 2.3 대응
        """
        if not s3_uri or not s3_uri.strip():
            raise InvalidInputError("동영상 URI가 제공되지 않았습니다")
        
        # URI 정규화
        uri = s3_uri.strip()
        
        # 기본적인 URI 형식 검증은 NovaProLLM에서 수행
        return uri

    def _get_analysis_instruction(self) -> str:
        """
        분석 지시사항 생성
        요구사항 2.2: 텍스트 추출, 주요 내용 요약, 키워드 추출
        """
        return """
        이 동영상을 분석하여 다음 정보를 추출해주세요:

        1. 텍스트 추출: 동영상에서 들리는 모든 음성 내용과 화면에 표시되는 텍스트
        2. 주요 내용 요약: 동영상의 핵심 내용과 메시지를 간결하게 요약
        3. 키워드 추출: 동영상 내용을 대표하는 주요 키워드들
        4. 구조적 정보: 동영상의 구성, 장면 전환, 시간대별 주요 내용

        결과는 구조화된 형태로 제공해주세요.
        """

    def _structure_analysis_result(self, response: Dict[str, Any], s3_uri: str) -> Dict[str, Any]:
        """
        분석 결과를 구조화된 형태로 변환
        요구사항 2.4: 분석 결과를 다른 분석과 동일한 형식으로 구조화
        """
        try:
            # LLM 응답에서 실제 분석 내용 추출
            analysis_content = response.get('analysis_result', '') if response else ''
            
            # None이나 빈 문자열 처리
            if not analysis_content:
                analysis_content = "동영상 분석 결과를 가져올 수 없습니다. 파일이 손상되었거나 지원되지 않는 형식일 수 있습니다."

            # 구조화된 결과 생성
            structured_result = {
                "extracted_text": self._extract_text_content(analysis_content),
                "content_summary": self._extract_summary(analysis_content),
                "keywords": self._extract_keywords(analysis_content),
                "structural_info": self._extract_structural_info(analysis_content),
                "raw_analysis": analysis_content,
                "confidence_score": self._calculate_confidence_score(analysis_content)
            }

            # 결과 검증
            self._validate_structured_result(structured_result)
            
            return structured_result
            
        except Exception as e:
            raise VideoAnalysisError(f"분석 결과 구조화 중 오류 발생: {str(e)}")

    def _extract_text_content(self, analysis: str) -> Dict[str, Any]:
        """텍스트 내용 추출"""
        # None 체크
        if not analysis:
            return {
                "speech_content": "",
                "screen_text": "",
                "total_text_length": 0
            }
        
        # 음성 내용과 화면 텍스트를 구분하여 추출
        return {
            "speech_content": self._extract_section(analysis, "음성|대화|말|발언"),
            "screen_text": self._extract_section(analysis, "화면|텍스트|자막|제목"),
            "total_text_length": len(analysis)
        }

    def _extract_summary(self, analysis: str) -> Dict[str, Any]:
        """주요 내용 요약 추출"""
        # None 체크
        if not analysis:
            return {
                "main_summary": "동영상 분석 결과를 가져올 수 없습니다.",
                "key_points": [],
                "overall_theme": ""
            }
        
        return {
            "main_summary": self._extract_section(analysis, "요약|핵심|주요내용|메인"),
            "key_points": self._extract_key_points(analysis),
            "overall_theme": self._extract_section(analysis, "주제|테마|목적")
        }

    def _extract_keywords(self, analysis: str) -> List[str]:
        """키워드 추출"""
        # None 체크
        if not analysis:
            return ['동영상', '분석', '오류']
        
        # 키워드 섹션에서 추출하거나 텍스트 분석을 통해 추출
        keywords_section = self._extract_section(analysis, "키워드|핵심어|태그")
        
        keywords = []
        if keywords_section:
            # 쉼표, 세미콜론, 줄바꿈으로 구분된 키워드들 추출
            # 한글, 영문, 숫자로 구성된 단어들 추출 (2글자 이상)
            potential_keywords = re.findall(r'[가-힣a-zA-Z0-9]{2,}', keywords_section)
            
            # 불용어 제거 및 정제
            stopwords = {'키워드', '핵심어', '태그', '내용', '분석', '결과', '정보'}
            keywords = [kw for kw in potential_keywords if kw not in stopwords and len(kw) >= 2]
            
            # 중복 제거 및 최대 20개
            keywords = list(dict.fromkeys(keywords))[:20]
        
        # 키워드가 없으면 전체 텍스트에서 중요한 단어들 추출
        if not keywords and analysis:
            # 자주 등장하는 의미있는 단어들 추출
            words = re.findall(r'[가-힣a-zA-Z0-9]{3,}', analysis)
            word_freq = {}
            for word in words:
                if word not in {'키워드', '분석', '결과', '내용', '정보', '시스템', '기능'}:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # 빈도순으로 정렬하여 상위 10개 선택
            keywords = sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:10]
        
        # 여전히 키워드가 없으면 기본값 반환
        if not keywords:
            keywords = ['동영상', '분석']
        
        return keywords

    def _extract_structural_info(self, analysis: str) -> Dict[str, Any]:
        """구조적 정보 추출"""
        # None 체크
        if not analysis:
            return {
                "video_sections": "",
                "scene_transitions": "",
                "timeline_info": ""
            }
        
        return {
            "video_sections": self._extract_section(analysis, "구성|섹션|단계|부분"),
            "scene_transitions": self._extract_section(analysis, "장면|전환|변화"),
            "timeline_info": self._extract_section(analysis, "시간|타임라인|순서")
        }

    def _extract_section(self, text: str, pattern: str) -> str:
        """특정 패턴과 관련된 섹션 추출"""
        # None 체크
        if not text or not pattern:
            return ""
        
        lines = text.split('\n')
        relevant_lines = []
        
        for line in lines:
            if re.search(pattern, line, re.IGNORECASE):
                relevant_lines.append(line.strip())
        
        return '\n'.join(relevant_lines) if relevant_lines else ""

    def _extract_key_points(self, analysis: str) -> List[str]:
        """주요 포인트들을 리스트로 추출"""
        # None 체크
        if not analysis:
            return []
        
        # 번호나 불릿 포인트로 시작하는 라인들 추출
        lines = analysis.split('\n')
        key_points = []
        
        for line in lines:
            line = line.strip()
            if re.match(r'^[\d\-\*\•]\s*', line) or '주요' in line or '핵심' in line:
                key_points.append(line)
        
        return key_points[:10]  # 최대 10개

    def _calculate_confidence_score(self, analysis: str) -> float:
        """분석 결과의 신뢰도 점수 계산"""
        # None 체크
        if not analysis:
            return 0.1  # 최소 신뢰도
        
        score = 0.5  # 기본 점수
        
        # 분석 내용의 길이에 따른 점수 조정
        if len(analysis) > 1000:
            score += 0.2
        elif len(analysis) > 500:
            score += 0.1
        
        # 구조화된 정보의 존재 여부에 따른 점수 조정
        structure_indicators = ["요약", "키워드", "주요", "핵심", "내용"]
        found_indicators = sum(1 for indicator in structure_indicators if indicator in analysis)
        score += min(found_indicators * 0.05, 0.3)
        
        return min(score, 1.0)

    def _validate_structured_result(self, result: Dict[str, Any]) -> None:
        """구조화된 결과 검증"""
        required_fields = ["extracted_text", "content_summary", "keywords", "structural_info"]
        
        for field in required_fields:
            if field not in result:
                raise VideoAnalysisError(f"필수 필드 '{field}'가 결과에 없습니다")
        
        # 최소한의 내용이 있는지 확인
        if not result.get("raw_analysis") or len(result["raw_analysis"]) < 50:
            raise VideoAnalysisError("분석 결과가 너무 짧거나 비어있습니다")

    def _create_error_response(self, error_type: str, message: str, s3_uri: str) -> Dict[str, Any]:
        """
        오류 응답 생성
        요구사항 2.3: 적절한 오류 메시지 반환
        """
        error_messages = {
            "invalid_input": "입력된 URI가 올바르지 않습니다. S3 URI 형식을 확인해주세요.",
            "unsupported_format": "지원하지 않는 동영상 형식입니다. MP4, MOV, AVI 등의 형식을 사용해주세요.",
            "analysis_error": "동영상 분석 중 문제가 발생했습니다. 파일이 손상되었거나 접근할 수 없을 수 있습니다.",
            "system_error": "시스템 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        }
        
        user_friendly_message = error_messages.get(error_type, message)
        
        return {
            "status": "error",
            "error_type": error_type,
            "reason": user_friendly_message,
            "technical_details": message,
            "data": {},
            "analysis_type": "video_analysis",
            "metadata": {
                "source_uri": s3_uri,
                "processing_timestamp": self._get_current_timestamp(),
                "error_occurred": True
            }
        }

    def _get_current_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        import datetime
        return datetime.datetime.now().isoformat()

    def extract_meaningful_content(self, s3_uri: str) -> Dict[str, Any]:
        """
        의미있는 내용 추출을 위한 전용 메서드
        요구사항 2.1, 2.2 대응
        """
        result = self.process(s3_uri)
        
        if result["status"] == "completed":
            data = result["data"]
            return {
                "text_content": data.get("extracted_text", {}),
                "summary": data.get("content_summary", {}),
                "keywords": data.get("keywords", []),
                "confidence": data.get("confidence_score", 0.0)
            }
        else:
            return {
                "error": result.get("reason", "분석 실패"),
                "error_type": result.get("error_type", "unknown")
            }