# -*- coding: utf-8 -*-
"""
분석 결과 시각화 모듈
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any, Optional
import json
from datetime import datetime


class ResultVisualizer:
    """분석 결과를 시각화하는 클래스"""
    
    def __init__(self):
        self.color_scheme = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e', 
            'success': '#2ca02c',
            'warning': '#d62728',
            'info': '#9467bd'
        }
        
        # 평가 항목별 한국어 이름
        self.category_names = {
            'business_value': '비즈니스 가치',
            'technical_feasibility': '기술적 실현가능성',
            'innovation': '혁신성',
            'user_engagement': '사용자 참여도',
            'accessibility': '접근성',
            'social_impact': '사회적 영향',
            'sustainability': '지속가능성',
            'network_effect': '네트워크 효과',
            'cost_analysis': '비용 분석'
        }
    
    def render_results(self, results: Dict[str, Any]) -> None:
        """분석 결과 전체 렌더링"""
        if not results:
            st.error("표시할 결과가 없습니다.")
            return
        
        # 결과 개요
        self._render_overview(results)
        
        st.markdown("---")
        
        # 점수 시각화
        col1, col2 = st.columns([2, 1])
        
        with col1:
            self._render_score_charts(results)
        
        with col2:
            self._render_score_summary(results)
        
        st.markdown("---")
        
        # 상세 분석 결과
        self._render_detailed_results(results)
        
        st.markdown("---")
        
        # 프로젝트 분류 정보
        self._render_classification_info(results)
        
        st.markdown("---")
        
        # 결과 다운로드 섹션
        self._render_download_section(results)
    
    def _render_overview(self, results: Dict[str, Any]) -> None:
        """결과 개요 렌더링"""
        st.header("📊 분석 결과 개요")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            final_score = results.get('final_score', 0)
            st.metric(
                label="최종 점수",
                value=f"{final_score:.2f}/10",
                delta=f"{final_score - 5:.2f}" if final_score != 5 else None
            )
        
        with col2:
            project_type = results.get('project_type', 'Unknown').upper()
            st.metric(
                label="프로젝트 유형",
                value=project_type
            )
        
        with col3:
            classification = results.get('classification', {})
            confidence = classification.get('confidence', 0)
            st.metric(
                label="분류 신뢰도",
                value=f"{confidence:.1%}"
            )
        
        with col4:
            timestamp = results.get('timestamp', '')
            if timestamp:
                analysis_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                st.metric(
                    label="분석 완료 시간",
                    value=analysis_time.strftime("%H:%M:%S")
                )
    
    def _render_score_charts(self, results: Dict[str, Any]) -> None:
        """점수 차트 렌더링"""
        st.subheader("📈 평가 점수 시각화")
        
        scores = results.get('scores', {})
        weighted_scores = results.get('weighted_scores', {})
        weights = results.get('weights', {})
        
        if not scores:
            st.warning("점수 데이터가 없습니다.")
            return
        
        # 탭으로 다양한 차트 제공
        tab1, tab2, tab3 = st.tabs(["레이더 차트", "막대 차트", "가중치 비교"])
        
        with tab1:
            self._render_radar_chart(scores, weighted_scores)
        
        with tab2:
            self._render_bar_chart(scores, weighted_scores, weights)
        
        with tab3:
            self._render_weight_comparison(scores, weighted_scores, weights)
    
    def _render_radar_chart(self, scores: Dict[str, float], weighted_scores: Dict[str, float]) -> None:
        """레이더 차트 렌더링"""
        categories = list(scores.keys())
        category_labels = [self.category_names.get(cat, cat) for cat in categories]
        
        # 원본 점수와 가중치 적용 점수
        original_values = [scores[cat] for cat in categories]
        weighted_values = [weighted_scores.get(cat, 0) for cat in categories]
        
        fig = go.Figure()
        
        # 원본 점수
        fig.add_trace(go.Scatterpolar(
            r=original_values,
            theta=category_labels,
            fill='toself',
            name='원본 점수',
            line_color=self.color_scheme['primary'],
            fillcolor=f"rgba(31, 119, 180, 0.3)"
        ))
        
        # 가중치 적용 점수
        fig.add_trace(go.Scatterpolar(
            r=weighted_values,
            theta=category_labels,
            fill='toself',
            name='가중치 적용 점수',
            line_color=self.color_scheme['secondary'],
            fillcolor=f"rgba(255, 127, 14, 0.3)"
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )
            ),
            showlegend=True,
            title="평가 항목별 점수 비교",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_bar_chart(self, scores: Dict[str, float], weighted_scores: Dict[str, float], 
                         weights: Dict[str, float]) -> None:
        """막대 차트 렌더링"""
        categories = list(scores.keys())
        category_labels = [self.category_names.get(cat, cat) for cat in categories]
        
        df = pd.DataFrame({
            '평가 항목': category_labels,
            '원본 점수': [scores[cat] for cat in categories],
            '가중치 적용 점수': [weighted_scores.get(cat, 0) for cat in categories],
            '가중치': [weights.get(cat, 0) for cat in categories]
        })
        
        # 점수 비교 막대 차트
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='원본 점수',
            x=df['평가 항목'],
            y=df['원본 점수'],
            marker_color=self.color_scheme['primary']
        ))
        
        fig.add_trace(go.Bar(
            name='가중치 적용 점수',
            x=df['평가 항목'],
            y=df['가중치 적용 점수'],
            marker_color=self.color_scheme['secondary']
        ))
        
        fig.update_layout(
            title='평가 항목별 점수 비교',
            xaxis_title='평가 항목',
            yaxis_title='점수',
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 데이터 테이블
        st.subheader("📋 상세 점수 표")
        st.dataframe(df, use_container_width=True)
    
    def _render_weight_comparison(self, scores: Dict[str, float], weighted_scores: Dict[str, float], 
                                 weights: Dict[str, float]) -> None:
        """가중치 비교 차트 렌더링"""
        categories = list(scores.keys())
        category_labels = [self.category_names.get(cat, cat) for cat in categories]
        
        # 가중치 파이 차트
        fig = go.Figure(data=[go.Pie(
            labels=category_labels,
            values=[weights.get(cat, 0) for cat in categories],
            hole=0.3,
            textinfo='label+percent',
            textposition='outside'
        )])
        
        fig.update_layout(
            title="평가 항목별 가중치 분포",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 가중치 효과 분석
        st.subheader("⚖️ 가중치 효과 분석")
        
        for cat in categories:
            original = scores[cat]
            weighted = weighted_scores.get(cat, 0)
            weight = weights.get(cat, 0)
            effect = weighted - original
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.write(f"**{self.category_names.get(cat, cat)}**")
            with col2:
                st.write(f"가중치: {weight:.3f}")
            with col3:
                st.write(f"효과: {effect:+.2f}")
            with col4:
                if effect > 0:
                    st.success("↗️ 상승")
                elif effect < 0:
                    st.error("↘️ 하락")
                else:
                    st.info("→ 동일")
    
    def _render_score_summary(self, results: Dict[str, Any]) -> None:
        """점수 요약 렌더링"""
        st.subheader("🎯 점수 요약")
        
        final_score = results.get('final_score', 0)
        
        # 점수 등급 계산
        if final_score >= 8.0:
            grade = "A"
            grade_color = "success"
            grade_desc = "우수"
        elif final_score >= 6.0:
            grade = "B"
            grade_color = "info"
            grade_desc = "양호"
        elif final_score >= 4.0:
            grade = "C"
            grade_color = "warning"
            grade_desc = "보통"
        else:
            grade = "D"
            grade_color = "error"
            grade_desc = "개선 필요"
        
        # 등급 표시
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; border-radius: 10px; 
                    background-color: {'#d4edda' if grade_color == 'success' else 
                                     '#d1ecf1' if grade_color == 'info' else
                                     '#fff3cd' if grade_color == 'warning' else '#f8d7da'};">
            <h2 style="margin: 0; color: {'#155724' if grade_color == 'success' else 
                                        '#0c5460' if grade_color == 'info' else
                                        '#856404' if grade_color == 'warning' else '#721c24'};">
                등급: {grade}
            </h2>
            <p style="margin: 5px 0; font-size: 18px;">{grade_desc}</p>
            <p style="margin: 0; font-size: 24px; font-weight: bold;">{final_score:.2f}/10</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 상위/하위 항목
        scores = results.get('scores', {})
        if scores:
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            
            st.subheader("🏆 상위 3개 항목")
            for i, (category, score) in enumerate(sorted_scores[:3]):
                st.write(f"{i+1}. {self.category_names.get(category, category)}: {score:.2f}")
            
            st.subheader("📉 하위 3개 항목")
            for i, (category, score) in enumerate(sorted_scores[-3:]):
                st.write(f"{len(sorted_scores)-2+i}. {self.category_names.get(category, category)}: {score:.2f}")
    
    def _render_detailed_results(self, results: Dict[str, Any]) -> None:
        """상세 분석 결과 렌더링"""
        st.subheader("🔍 상세 분석 결과")
        
        evaluation_results = results.get('evaluation_results', {})
        
        if not evaluation_results:
            st.warning("상세 분석 결과가 없습니다.")
            return
        
        # 각 평가 항목별 상세 정보
        for category, result in evaluation_results.items():
            if not isinstance(result, dict):
                continue
            
            with st.expander(f"📋 {self.category_names.get(category, category)} 상세 정보"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    score = result.get('score', result.get('total_score', 0))
                    st.metric("점수", f"{score:.2f}/10")
                    
                    execution_time = result.get('execution_time', 0)
                    if execution_time:
                        st.metric("실행 시간", f"{execution_time:.3f}초")
                
                with col2:
                    reasoning = result.get('reasoning', '')
                    if reasoning:
                        st.write("**평가 근거:**")
                        st.write(reasoning)
                
                # 개선 제안
                suggestions = result.get('suggestions', [])
                if suggestions:
                    st.write("**개선 제안:**")
                    for i, suggestion in enumerate(suggestions, 1):
                        st.write(f"{i}. {suggestion}")
                
                # 데이터 제한사항
                limitations = result.get('data_limitations', '')
                if limitations:
                    st.warning(f"**데이터 제한사항:** {limitations}")
                
                # 오류 정보
                error = result.get('error', '')
                if error:
                    st.error(f"**오류:** {error}")
    
    def _render_classification_info(self, results: Dict[str, Any]) -> None:
        """프로젝트 분류 정보 렌더링"""
        st.subheader("🏷️ 프로젝트 분류 정보")
        
        classification = results.get('classification', {})
        
        if not classification:
            st.warning("분류 정보가 없습니다.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**분류 결과:**")
            project_type = classification.get('project_type', 'Unknown')
            confidence = classification.get('confidence', 0)
            
            st.info(f"""
            - **프로젝트 유형:** {project_type.upper()}
            - **신뢰도:** {confidence:.1%}
            - **PainKiller 점수:** {classification.get('painkiller_score', 0):.3f}
            - **Vitamin 점수:** {classification.get('vitamin_score', 0):.3f}
            """)
            
            warning_message = classification.get('warning_message', '')
            if warning_message:
                st.warning(f"**주의사항:** {warning_message}")
        
        with col2:
            st.write("**분류 근거:**")
            reasoning = classification.get('reasoning', '분류 근거가 없습니다.')
            st.write(reasoning)
        
        # 가중치 정보
        weight_summary = results.get('weight_summary', '')
        if weight_summary:
            st.write("**적용된 가중치 정보:**")
            st.code(weight_summary)
    
    def _render_download_section(self, results: Dict[str, Any]) -> None:
        """결과 다운로드 섹션 렌더링"""
        st.subheader("💾 결과 다운로드")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # JSON 다운로드
            json_data = json.dumps(results, ensure_ascii=False, indent=2)
            st.download_button(
                label="📄 JSON 다운로드",
                data=json_data,
                file_name=f"analysis_result_{results.get('session_id', 'unknown')}.json",
                mime="application/json"
            )
        
        with col2:
            # CSV 다운로드 (점수 데이터)
            scores = results.get('scores', {})
            if scores:
                df = pd.DataFrame([
                    {
                        '평가항목': self.category_names.get(cat, cat),
                        '원본점수': score,
                        '가중치': results.get('weights', {}).get(cat, 0),
                        '가중치적용점수': results.get('weighted_scores', {}).get(cat, 0)
                    }
                    for cat, score in scores.items()
                ])
                
                csv_data = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📊 CSV 다운로드",
                    data=csv_data,
                    file_name=f"analysis_scores_{results.get('session_id', 'unknown')}.csv",
                    mime="text/csv"
                )
        
        with col3:
            # 요약 보고서 다운로드
            report = self._generate_summary_report(results)
            st.download_button(
                label="📋 요약 보고서",
                data=report,
                file_name=f"analysis_report_{results.get('session_id', 'unknown')}.txt",
                mime="text/plain"
            )
    
    def _generate_summary_report(self, results: Dict[str, Any]) -> str:
        """요약 보고서 생성"""
        report_lines = [
            "=" * 50,
            "프로젝트 평가 결과 요약 보고서",
            "=" * 50,
            "",
            f"분석 일시: {results.get('timestamp', 'Unknown')}",
            f"세션 ID: {results.get('session_id', 'Unknown')}",
            "",
            "=" * 30,
            "1. 전체 결과",
            "=" * 30,
            f"최종 점수: {results.get('final_score', 0):.2f}/10",
            f"프로젝트 유형: {results.get('project_type', 'Unknown').upper()}",
            "",
            "=" * 30,
            "2. 항목별 점수",
            "=" * 30,
        ]
        
        scores = results.get('scores', {})
        for category, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            category_name = self.category_names.get(category, category)
            report_lines.append(f"{category_name}: {score:.2f}/10")
        
        report_lines.extend([
            "",
            "=" * 30,
            "3. 분류 정보",
            "=" * 30,
        ])
        
        classification = results.get('classification', {})
        if classification:
            report_lines.extend([
                f"프로젝트 유형: {classification.get('project_type', 'Unknown')}",
                f"분류 신뢰도: {classification.get('confidence', 0):.1%}",
                f"분류 근거: {classification.get('reasoning', 'N/A')}",
            ])
        
        report_lines.extend([
            "",
            "=" * 50,
            "보고서 끝",
            "=" * 50
        ])
        
        return "\n".join(report_lines)