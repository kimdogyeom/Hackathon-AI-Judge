
# -*- coding: utf-8 -*-
import re
import yaml
from typing import Dict, Any, List
from .base_evaluation_chain import EvaluationChainBase


class AccessibilityChain(EvaluationChainBase):
    """
    접근성 평가 체인.
    WCAG 가이드라인을 기반으로 프로젝트의 접근성을 평가합니다.
    """

    def __init__(self, config_path: str = "src/config/evaluation.yaml"):
        super().__init__("AccessibilityChain")
        self._load_evaluation_criteria(config_path)
        
        # WCAG 2.1 기준 평가 키워드 (기존 로직과 병행 사용)
        self.accessibility_keywords = {
            # 인식 가능성 (Perceivable)
            "perceivable": [
                "대체 텍스트", "alt text", "스크린 리더", "screen reader",
                "색상 대비", "color contrast", "자막", "caption", "수화",
                "시각 장애", "청각 장애", "색맹", "colorblind"
            ],
            # 운용 가능성 (Operable)
            "operable": [
                "키보드 네비게이션", "keyboard navigation", "포커스", "focus",
                "마우스 없이", "without mouse", "탭 순서", "tab order",
                "접근 키", "access key", "단축키", "shortcut"
            ],
            # 이해 가능성 (Understandable)
            "understandable": [
                "명확한 언어", "clear language", "간단한 설명", "simple explanation",
                "사용자 가이드", "user guide", "도움말", "help", "오류 메시지",
                "error message", "입력 도움", "input help"
            ],
            # 견고성 (Robust)
            "robust": [
                "호환성", "compatibility", "다양한 브라우저", "multiple browsers",
                "보조 기술", "assistive technology", "웹 표준", "web standards",
                "HTML 유효성", "HTML validation", "시맨틱", "semantic"
            ]
        }
        
        # 접근성 관련 부정적 키워드
        self.negative_keywords = [
            "접근성 고려 안함", "accessibility not considered",
            "시각적으로만", "visual only", "마우스 필수", "mouse required",
            "복잡한 인터페이스", "complex interface", "작은 글씨", "small text"
        ]

    def _load_evaluation_criteria(self, config_path: str):
        """evaluation.yaml에서 Accessibility 평가 기준을 로드합니다."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                criteria = yaml.safe_load(file)
            
            accessibility = criteria.get('Accessibility', {})
            self.pain_killer_criteria = accessibility.get('pain_killer', [])
            self.vitamin_criteria = accessibility.get('vitamin', [])
            
        except Exception as e:
            self.logger.warning(f"평가 기준 로드 실패, 기본값 사용: {e}")
            self.pain_killer_criteria = [
                "타겟 사용자에게 쉬운 접근성을 제공하는가?",
                "접근성 개선의 필요성과 중요성이 높은가?"
            ]
            self.vitamin_criteria = [
                "편리함/포용성을 개선하는가?",
                "다양한 사용자층(소외 계층)을 포용하는가?"
            ]

    def _analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        WCAG 가이드라인 기반 접근성 분석 수행.
        
        Args:
            data: 분석할 프로젝트 데이터
            
        Returns:
            Dict: 접근성 평가 결과
        """
        # 데이터 제한사항 확인
        limitations = self._check_data_availability(data)
        
        # 각 WCAG 원칙별 점수 계산
        perceivable_score = self._evaluate_perceivable(data)
        operable_score = self._evaluate_operable(data)
        understandable_score = self._evaluate_understandable(data)
        robust_score = self._evaluate_robust(data)
        
        # 전체 점수 계산 (각 원칙별 가중치 적용)
        total_score = (
            perceivable_score * 0.3 +    # 인식 가능성 30%
            operable_score * 0.3 +       # 운용 가능성 30%
            understandable_score * 0.25 + # 이해 가능성 25%
            robust_score * 0.15          # 견고성 15%
        )
        
        # 점수를 0-10 범위로 조정
        final_score = min(10.0, max(0.0, total_score))
        
        # 평가 근거 생성
        reasoning = self._generate_reasoning(
            perceivable_score, operable_score, 
            understandable_score, robust_score, data
        )
        
        # 개선 제안 생성
        suggestions = self._generate_suggestions(
            perceivable_score, operable_score,
            understandable_score, robust_score, data
        )
        
        result = {
            "score": final_score,
            "reasoning": reasoning,
            "suggestions": suggestions,
            "detailed_scores": {
                "perceivable": perceivable_score,
                "operable": operable_score,
                "understandable": understandable_score,
                "robust": robust_score
            }
        }
        
        # 데이터 제한사항이 있는 경우 추가
        if limitations:
            result["data_limitations"] = "; ".join(limitations)
        
        return result

    def _evaluate_perceivable(self, data: Dict[str, Any]) -> float:
        """인식 가능성 평가 (WCAG 원칙 1)"""
        score = 0.0
        content = self._extract_all_content(data)
        
        # 대체 텍스트 및 스크린 리더 지원 언급
        if self._contains_keywords(content, self.accessibility_keywords["perceivable"][:4]):
            score += 4.0
        
        # 색상 대비 및 시각적 접근성 고려
        if self._contains_keywords(content, self.accessibility_keywords["perceivable"][4:8]):
            score += 3.0
        
        # 청각 장애인 지원 (자막, 수화 등)
        if self._contains_keywords(content, self.accessibility_keywords["perceivable"][8:]):
            score += 3.0
        
        # 시각적 요소만 강조하는 경우 감점
        if "시각적으로만" in content or "visual only" in content.lower():
            score -= 1.0
        
        return min(10.0, max(0.0, score))

    def _evaluate_operable(self, data: Dict[str, Any]) -> float:
        """운용 가능성 평가 (WCAG 원칙 2)"""
        score = 0.0
        content = self._extract_all_content(data)
        
        # 키보드 네비게이션 지원
        if self._contains_keywords(content, self.accessibility_keywords["operable"][:6]):
            score += 6.0
        
        # 접근 키 및 단축키 지원
        if self._contains_keywords(content, self.accessibility_keywords["operable"][6:]):
            score += 4.0
        
        # 마우스 필수 사용 언급 시 감점
        if "마우스 필수" in content or "mouse required" in content.lower():
            score -= 2.0
        
        return min(10.0, max(0.0, score))

    def _evaluate_understandable(self, data: Dict[str, Any]) -> float:
        """이해 가능성 평가 (WCAG 원칙 3)"""
        score = 0.0
        content = self._extract_all_content(data)
        
        # 명확한 언어 및 설명 사용
        if self._contains_keywords(content, self.accessibility_keywords["understandable"][:4]):
            score += 4.0
        
        # 사용자 가이드 및 도움말 제공
        if self._contains_keywords(content, self.accessibility_keywords["understandable"][4:8]):
            score += 4.0
        
        # 오류 처리 및 입력 도움 제공
        if self._contains_keywords(content, self.accessibility_keywords["understandable"][8:]):
            score += 2.0
        
        # 복잡한 인터페이스 언급 시 감점
        if "복잡한 인터페이스" in content or "complex interface" in content.lower():
            score -= 1.0
        
        return min(10.0, max(0.0, score))

    def _evaluate_robust(self, data: Dict[str, Any]) -> float:
        """견고성 평가 (WCAG 원칙 4)"""
        score = 0.0
        content = self._extract_all_content(data)
        
        # 호환성 및 다양한 브라우저 지원
        if self._contains_keywords(content, self.accessibility_keywords["robust"][:4]):
            score += 5.0
        
        # 보조 기술 및 웹 표준 준수
        if self._contains_keywords(content, self.accessibility_keywords["robust"][4:]):
            score += 5.0
        
        return min(10.0, max(0.0, score))

    def _extract_all_content(self, data: Dict[str, Any]) -> str:
        """모든 입력 데이터에서 텍스트 내용을 추출"""
        content_parts = []
        
        # 각 분석 결과에서 내용 추출
        for analysis_type in ["video_analysis", "document_analysis", "presentation_analysis"]:
            analysis_data = data.get(analysis_type, {})
            if isinstance(analysis_data, dict):
                content = analysis_data.get("content", "")
                if content:
                    content_parts.append(str(content))
        
        # 직접 content가 있는 경우
        if "content" in data:
            content_parts.append(str(data["content"]))
        
        return " ".join(content_parts).lower()

    def _contains_keywords(self, content: str, keywords: List[str]) -> bool:
        """텍스트에 키워드가 포함되어 있는지 확인"""
        content_lower = content.lower()
        return any(keyword.lower() in content_lower for keyword in keywords)

    def _generate_reasoning(self, perceivable: float, operable: float, 
                          understandable: float, robust: float, data: Dict[str, Any]) -> str:
        """평가 근거 생성"""
        content = self._extract_all_content(data)
        reasoning_parts = []
        
        # 각 WCAG 원칙별 평가 근거
        if perceivable >= 5.0:
            reasoning_parts.append("인식 가능성 측면에서 대체 텍스트, 색상 대비 등 시각/청각 장애인을 위한 고려사항이 잘 반영됨")
        elif perceivable >= 3.0:
            reasoning_parts.append("인식 가능성 측면에서 기본적인 접근성 고려사항은 있으나 개선 여지가 있음")
        else:
            reasoning_parts.append("인식 가능성 측면에서 시각/청각 장애인을 위한 접근성 고려가 부족함")
        
        if operable >= 4.0:
            reasoning_parts.append("키보드 네비게이션 등 운용 가능성이 잘 고려됨")
        elif operable >= 2.0:
            reasoning_parts.append("운용 가능성 측면에서 기본적인 고려는 있으나 키보드 접근성 개선 필요")
        else:
            reasoning_parts.append("키보드만으로 조작 가능한 인터페이스 설계가 부족함")
        
        if understandable >= 5.0:
            reasoning_parts.append("사용자 가이드와 명확한 설명으로 이해 가능성이 높음")
        elif understandable >= 3.0:
            reasoning_parts.append("이해 가능성 측면에서 기본적인 설명은 제공되나 더 명확한 가이드 필요")
        else:
            reasoning_parts.append("사용자 이해를 돕는 명확한 설명과 가이드가 부족함")
        
        if robust >= 3.0:
            reasoning_parts.append("다양한 환경과 보조 기술에서의 호환성이 고려됨")
        else:
            reasoning_parts.append("다양한 브라우저와 보조 기술과의 호환성 고려가 부족함")
        
        return "; ".join(reasoning_parts)

    def _generate_suggestions(self, perceivable: float, operable: float,
                            understandable: float, robust: float, data: Dict[str, Any]) -> List[str]:
        """개선 제안 생성"""
        suggestions = []
        
        # 인식 가능성 개선 제안
        if perceivable < 5.0:
            suggestions.extend([
                "모든 이미지와 미디어에 대체 텍스트 제공",
                "색상 대비비를 WCAG 2.1 AA 기준(4.5:1) 이상으로 조정",
                "비디오 콘텐츠에 자막 및 수화 통역 제공"
            ])
        
        # 운용 가능성 개선 제안
        if operable < 4.0:
            suggestions.extend([
                "키보드만으로 모든 기능 접근 가능하도록 개선",
                "논리적인 탭 순서 설정 및 포커스 표시 명확화",
                "마우스 호버 기능에 키보드 대안 제공"
            ])
        
        # 이해 가능성 개선 제안
        if understandable < 5.0:
            suggestions.extend([
                "명확하고 간단한 언어로 사용자 인터페이스 작성",
                "상세한 사용자 가이드 및 도움말 시스템 구축",
                "입력 오류 시 구체적인 수정 방법 안내"
            ])
        
        # 견고성 개선 제안
        if robust < 3.0:
            suggestions.extend([
                "웹 표준 준수 및 HTML 유효성 검증",
                "다양한 브라우저와 보조 기술에서 테스트 수행",
                "시맨틱 HTML 사용으로 구조적 접근성 향상"
            ])
        
        # 일반적인 개선 제안
        if not suggestions:
            suggestions.append("현재 접근성 수준을 유지하며 정기적인 접근성 테스트 수행")
        
        return suggestions[:5]  # 최대 5개 제안으로 제한

