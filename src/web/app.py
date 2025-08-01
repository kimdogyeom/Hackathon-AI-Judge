# -*- coding: utf-8 -*-
"""
간단한 Streamlit 기반 웹 애플리케이션
"""
import streamlit as st
import tempfile
import os
from pathlib import Path
import json
from datetime import datetime

# plotly import를 상단으로 이동
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.error("Plotly가 설치되지 않았습니다. pip install plotly로 설치해주세요.")

# pandas import 문제 해결
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# 기존 시스템 모듈들 import
from src.analysis.video_analysis import VideoAnalysis
from src.analysis.document_analysis import DocumentAnalysis
from src.analysis.presentation_analysis import PresentationAnalysis
from src.classifier.project_type_classifier import ProjectTypeClassifier
from src.chain.chain_executor import ChainExecutor
from src.config.config_manager import get_config_manager


def main():
    """메인 함수"""
    st.set_page_config(
        page_title="프로젝트 평가 시스템",
        page_icon="📊",
        layout="wide"
    )
    
    # URL 파라미터 확인 (공유 링크 처리)
    query_params = st.query_params
    shared_result_id = query_params.get("share", None)
    
    if shared_result_id:
        # 공유된 결과 표시
        st.title("🔗 공유된 분석 결과")
        st.info(f"공유 ID: {shared_result_id}")
        
        # 실제로는 데이터베이스에서 결과를 조회해야 하지만, 
        # 여기서는 데모용으로 메시지만 표시
        st.warning("""
        **공유 기능 데모**
        
        실제 운영 환경에서는 다음과 같이 동작합니다:
        1. 공유 ID를 통해 데이터베이스에서 분석 결과 조회
        2. 결과가 존재하고 만료되지 않았다면 결과 표시
        3. 결과가 없거나 만료되었다면 오류 메시지 표시
        
        현재는 데모 환경이므로 실제 공유 데이터를 표시할 수 없습니다.
        """)
        
        if st.button("🏠 홈으로 돌아가기"):
            st.query_params.clear()
            st.rerun()
        
        return
        
    st.title("🚀 프로젝트 평가 시스템")
    st.markdown("---")
    
    # 세션 상태 초기화
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'analysis_in_progress' not in st.session_state:
        st.session_state.analysis_in_progress = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "파일 업로드"
    
    # 사이드바 메뉴 (버튼 방식)
    with st.sidebar:
        st.header("📋 메뉴")
        
        # 파일 업로드 버튼
        if st.button("📁 파일 업로드", use_container_width=True, 
                    type="primary" if st.session_state.current_page == "파일 업로드" else "secondary"):
            st.session_state.current_page = "파일 업로드"
            st.rerun()
        
        # 결과 확인 버튼
        if st.button("📈 결과 확인", use_container_width=True,
                    type="primary" if st.session_state.current_page == "결과 확인" else "secondary"):
            st.session_state.current_page = "결과 확인"
            st.rerun()

    # 페이지 렌더링
    if st.session_state.current_page == "파일 업로드":
        render_upload_page()
    elif st.session_state.current_page == "결과 확인":
        render_results_page()

def render_upload_page():
    """파일 업로드 페이지"""
    st.header("📁 파일 업로드 및 분석")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("프로젝트 자료 업로드")
        
        # 파일 업로드
        document_file = st.file_uploader(
            "📄 프로젝트 문서 (TXT/DOC/DOCX/RTF)",
            type=['txt', 'doc', 'docx', 'rtf'],
            help="프로젝트 설명이 포함된 문서 파일을 업로드하세요"
        )
        
        presentation_file = st.file_uploader(
            "📊 발표자료 (PDF/이미지)",
            type=['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp'],
            help="프로젝트 발표자료 PDF 파일 또는 이미지 파일을 업로드하세요"
        )
        
        video_file = st.file_uploader(
            "🎥 동영상 (MP4)",
            type=['mp4'],
            help="프로젝트 소개 동영상을 업로드하세요"
        )
        
        # 분석 시작 버튼
        if st.button("🔍 분석 시작", type="primary"):
            if document_file or presentation_file or video_file:
                with st.spinner("분석 중입니다... 잠시만 기다려주세요."):
                    results = run_analysis(document_file, presentation_file, video_file)
                    if results:
                        st.session_state.analysis_results = results
                        st.success("✅ 분석이 완료되었습니다!")
                        
                        # 3초 후 자동으로 결과 확인 페이지로 이동
                        import time
                        time.sleep(2)
                        st.session_state.current_page = "결과 확인"
                        st.rerun()
                    else:
                        st.error("❌ 분석 중 오류가 발생했습니다. 다시 시도해주세요.")
            else:
                st.warning("최소 1개 이상의 파일을 업로드해주세요.")
    
    with col2:
        st.subheader("📋 업로드 가이드")
        st.info("""
        **지원 파일 형식:**
        - 문서: TXT, DOC, DOCX, RTF (최대 100MB)
        - 발표자료: PDF, JPG, PNG, GIF 등 이미지 (최대 200MB)
        - 동영상: MP4, MOV, AVI 등 (최대 500MB)
        
        **권장사항:**
        - 최소 1개 이상의 파일 업로드
        - 명확한 프로젝트 설명 포함
        - 파일명은 영문으로 작성
        """)

def run_analysis(document_file, presentation_file, video_file):
    """분석 실행 - S3 업로드 방식"""
    try:
        # S3 업로드를 위한 임시 파일 저장 및 업로드
        temp_dir = Path(tempfile.mkdtemp())
        file_paths = {}
        s3_urls = {}
        
        # 파일 업로더 가져오기
        try:
            from src.config.config import get_file_uploader
            file_uploader = get_file_uploader()
        except Exception as e:
            st.error(f"파일 업로더 초기화 실패: {str(e)}")
            return None
        
        # 문서 파일 처리
        if document_file:
            doc_path = temp_dir / "document.txt"
            with open(doc_path, "wb") as f:
                f.write(document_file.getvalue())
            file_paths['document'] = str(doc_path)
            
            # S3에 업로드
            try:
                upload_result = file_uploader.upload_document(str(doc_path))
                s3_urls['document'] = upload_result['s3_url']
                st.info(f"✅ 문서 파일이 S3에 업로드되었습니다: {upload_result['s3_url']}")
            except Exception as e:
                st.warning(f"⚠️ 문서 파일 S3 업로드 실패: {str(e)}")
                s3_urls['document'] = None
        
        # 프레젠테이션 파일 처리
        if presentation_file:
            pres_path = temp_dir / "presentation.pdf"
            with open(pres_path, "wb") as f:
                f.write(presentation_file.getvalue())
            file_paths['presentation'] = str(pres_path)
            
            # S3에 업로드
            try:
                upload_result = file_uploader.upload_presentation(str(pres_path))
                s3_urls['presentation'] = upload_result['s3_url']
                st.info(f"✅ 프레젠테이션 파일이 S3에 업로드되었습니다: {upload_result['s3_url']}")
            except Exception as e:
                st.warning(f"⚠️ 프레젠테이션 파일 S3 업로드 실패: {str(e)}")
                s3_urls['presentation'] = None
        
        # 동영상 파일 처리
        if video_file:
            video_path = temp_dir / "video.mp4"
            with open(video_path, "wb") as f:
                f.write(video_file.getvalue())
            file_paths['video'] = str(video_path)
            
            # S3에 업로드
            try:
                upload_result = file_uploader.upload_video(str(video_path))
                s3_urls['video'] = upload_result['s3_url']
                st.info(f"✅ 동영상 파일이 S3에 업로드되었습니다: {upload_result['s3_url']}")
            except Exception as e:
                st.warning(f"⚠️ 동영상 파일 S3 업로드 실패: {str(e)}")
                s3_urls['video'] = None
        
        # 분석 실행 - 실시간 진행 상황 표시
        progress_container = st.container()
        with progress_container:
            st.subheader("🔄 분석 진행 상황")
            progress_bar = st.progress(0)
            status_text = st.empty()
            step_status = st.empty()
        
        # 1단계: 파일 분석
        with step_status.container():
            st.write("**현재 단계:** 파일 분석")
            st.write("- 업로드된 파일들을 읽고 내용을 추출합니다")
        status_text.text("1/4 파일 분석 중...")
        progress_bar.progress(25)
        
        import time
        time.sleep(1)  # 진행 상황을 보여주기 위한 지연
        
        analysis_results = {}
        
        # 간단한 더미 분석 결과 (실제로는 파일을 읽어서 분석)
        if 'document' in file_paths:
            with open(file_paths['document'], 'r', encoding='utf-8') as f:
                content = f.read()
            analysis_results['document_analysis'] = {
                'content': content[:500] + "..." if len(content) > 500 else content,
                'summary': '문서 분석 완료',
                'keywords': ['프로젝트', '개발', '시스템']
            }
        
        if 'presentation' in file_paths:
            analysis_results['presentation_analysis'] = {
                'content': '발표자료 분석 완료',
                'summary': 'PDF 발표자료가 업로드되었습니다.',
                'keywords': ['발표', '프레젠테이션', '자료']
            }
        
        if 'video' in file_paths and s3_urls.get('video'):
            # S3 URL을 사용하여 실제 동영상 분석 수행
            try:
                from src.analysis.video_analysis import VideoAnalysis
                video_analyzer = VideoAnalysis()
                video_result = video_analyzer.process(s3_urls['video'])
                
                if video_result['status'] == 'completed':
                    video_data = video_result['data']
                    analysis_results['video_analysis'] = {
                        'content': video_data.get('raw_analysis', '동영상 분석 완료'),
                        'summary': video_data.get('content_summary', {}).get('main_summary', '동영상이 분석되었습니다.'),
                        'keywords': video_data.get('keywords', ['동영상', '비디오', '미디어']),
                        's3_url': s3_urls['video'],
                        'confidence_score': video_data.get('confidence_score', 0.8)
                    }
                else:
                    # 분석 실패 시 기본값
                    analysis_results['video_analysis'] = {
                        'content': f"동영상 분석 실패: {video_result.get('reason', '알 수 없는 오류')}",
                        'summary': '동영상 분석 중 오류가 발생했습니다.',
                        'keywords': ['동영상', '오류'],
                        's3_url': s3_urls['video'],
                        'error': video_result.get('reason', '분석 실패')
                    }
            except Exception as e:
                st.warning(f"⚠️ 동영상 분석 중 오류 발생: {str(e)}")
                analysis_results['video_analysis'] = {
                    'content': f'동영상 분석 오류: {str(e)}',
                    'summary': '동영상 분석 중 시스템 오류가 발생했습니다.',
                    'keywords': ['동영상', '시스템오류'],
                    's3_url': s3_urls['video'],
                    'error': str(e)
                }
        elif 'video' in file_paths:
            # S3 업로드 실패한 경우
            analysis_results['video_analysis'] = {
                'content': '동영상 S3 업로드 실패로 인한 분석 불가',
                'summary': '동영상 파일을 S3에 업로드하지 못했습니다.',
                'keywords': ['동영상', '업로드실패'],
                'error': 'S3 업로드 실패'
            }
        
        # 2단계: 프로젝트 분류
        with step_status.container():
            st.write("**현재 단계:** 프로젝트 분류")
            st.write("- AI가 프로젝트 유형을 PainKiller/Vitamin으로 분류합니다")
        status_text.text("2/4 프로젝트 분류 중...")
        progress_bar.progress(50)
        time.sleep(1)
        
        classifier = ProjectTypeClassifier()
        try:
            classification_result = classifier.classify(analysis_results)
        except Exception as e:
            # 분류 실패시 명확한 오류 반환
            st.error(f"프로젝트 분류 실패: {str(e)}")
            return None
        
        # 3단계: 평가 체인 실행
        with step_status.container():
            st.write("**현재 단계:** 평가 체인 실행")
            st.write("- 9개 평가 항목에 대해 AI가 점수를 매깁니다")
            st.write("- 비즈니스 가치, 기술적 실현가능성, 혁신성 등을 평가합니다")
        status_text.text("3/4 평가 체인 실행 중...")
        progress_bar.progress(75)
        time.sleep(2)  # 가장 오래 걸리는 단계
        
        # 평가 체인 입력 데이터 준비 (S3 URL 및 분류 결과 포함)
        chain_input = {
            "project_type": classification_result.get('project_type', 'balanced'),
            "classification": classification_result,  # 전체 분류 결과
            "s3_urls": s3_urls,  # S3 URL 정보 추가
            **analysis_results
        }
        
        # 체인 실행기 초기화
        executor = ChainExecutor()
        
        # 진행 상황 업데이트 콜백 함수
        def update_progress(chain_name, current, total):
            chain_progress = 75 + ((current+1) / total) * 15  # 75%에서 90%까지
            progress_bar.progress(int(chain_progress))
            status_text.text(f"3/4 평가 체인 실행 중... ({current+1}/{total}) {chain_name}")
        
        # 콜백 설정
        executor.set_progress_callback(update_progress)
        
        # 모든 평가 체인 실행
        execution_result = executor.execute_all(chain_input)
        
        # 결과 추출
        evaluation_results = execution_result["results"]
        error_count = execution_result["metadata"]["error_count"]
        
        # 오류 발생 체인에 대한 경고 표시
        for chain_name, result in evaluation_results.items():
            if "error" in result:
                st.warning(f"⚠️ {chain_name} 평가 중 오류 발생: {result['error']}")
        
        # 오류 요약 표시
        if error_count > 0:
            st.error(f"⚠️ 총 {error_count}개의 평가 항목에서 오류가 발생했습니다. 기본값으로 처리되었습니다.")
        
        # 4단계: 최종 점수 계산
        with step_status.container():
            st.write("**현재 단계:** 최종 점수 계산")
            st.write("- 프로젝트 유형에 따른 가중치를 적용합니다")
            st.write("- 최종 종합 점수를 계산합니다")
        status_text.text("4/4 최종 점수 계산 중...")
        progress_bar.progress(100)
        time.sleep(1)
        
        # 점수 추출 및 가중치 적용
        config_manager = get_config_manager()
        project_type = classification_result['project_type']
        weights = config_manager.get_weights(project_type)
        
        # 체인 실행기로 점수 추출 및 계산
        scores = executor.get_scores(evaluation_results)
        weighted_scores = executor.apply_weights(scores, weights)
        final_score = executor.calculate_final_score(weighted_scores)
        
        # 결과 구성
        results = {
            'timestamp': datetime.now().isoformat(),
            'classification': classification_result,
            'evaluation_results': evaluation_results,
            'scores': scores,
            'weights': weights,
            'weighted_scores': weighted_scores,
            'final_score': final_score,
            'project_type': project_type,
            'weight_summary': f"{project_type} 유형 가중치 적용됨",
            'uploaded_files': {
                'document': document_file.name if document_file else None,
                'presentation': presentation_file.name if presentation_file else None,
                'video': video_file.name if video_file else None
            },
            's3_urls': s3_urls,  # S3 URL 정보 추가
            'file_paths': file_paths  # 로컬 파일 경로 (분석용)
        }
        
        # 임시 파일 정리
        import shutil
        shutil.rmtree(temp_dir)
        
        # 분석 완료
        with step_status.container():
            st.write("**분석 완료!** ✅")
            st.write("- 모든 분석이 성공적으로 완료되었습니다")
            st.write("- '결과 확인' 페이지에서 상세 결과를 확인하세요")
        
        status_text.text("✅ 분석 완료!")
        progress_bar.progress(100)
        
        return results
        
    except Exception as e:
        st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
        return None

def render_results_page():
    """결과 확인 페이지"""
    st.header("📈 분석 결과")
    
    if not st.session_state.analysis_results:
        st.info("분석 결과가 없습니다. 먼저 파일을 업로드하고 분석을 완료해주세요.")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("📁 파일 업로드 페이지로 이동", type="primary"):
                st.session_state.current_page = "파일 업로드"
                st.rerun()
        return
    
    results = st.session_state.analysis_results
    
    # 결과 개요
    st.subheader("📊 분석 결과 개요")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        final_score = results.get('final_score', 0)
        st.metric("최종 점수", f"{final_score:.2f}/10")
    
    with col2:
        project_type = results.get('project_type', 'Unknown').upper()
        st.metric("프로젝트 유형", project_type)
    
    with col3:
        classification = results.get('classification', {})
        confidence = classification.get('confidence', 0)
        st.metric("분류 신뢰도", f"{confidence:.1%}")
    
    with col4:
        uploaded_files = results.get('uploaded_files', {})
        file_count = sum(1 for f in uploaded_files.values() if f)
        st.metric("업로드된 파일", f"{file_count}개")
    
    st.markdown("---")
    
    # 점수 시각화
    st.subheader("📈 평가 결과 시각화")
    
    scores = results.get('scores', {})
    weighted_scores = results.get('weighted_scores', {})
    weights = results.get('weights', {})
    
    # 평가 항목 한국어 이름
    category_names = {
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
    
    # 탭으로 다양한 시각화 제공
    tab1, tab2, tab3 = st.tabs(["📊 막대 차트", "🎯 레이더 차트", "⚖️ 가중치 분석"])
    
    with tab1:
        if not PLOTLY_AVAILABLE:
            st.error("시각화를 위해 Plotly가 필요합니다.")
            return
            
        # 막대 차트
        categories = [category_names.get(cat, cat) for cat in scores.keys()]
        original_scores = list(scores.values())
        weighted_scores_list = [weighted_scores.get(cat, 0) for cat in scores.keys()]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='원본 점수',
            x=categories,
            y=original_scores,
            marker_color='lightblue'
        ))
        fig.add_trace(go.Bar(
            name='가중치 적용 점수',
            x=categories,
            y=weighted_scores_list,
            marker_color='darkblue'
        ))
        
        fig.update_layout(
            title='평가 항목별 점수 비교',
            xaxis_title='평가 항목',
            yaxis_title='점수',
            barmode='group',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True, key="bar_chart")
    
    with tab2:
        # 레이더 차트
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=original_scores,
            theta=categories,
            fill='toself',
            name='원본 점수',
            line_color='lightblue'
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=weighted_scores_list,
            theta=categories,
            fill='toself',
            name='가중치 적용 점수',
            line_color='darkblue'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )
            ),
            showlegend=True,
            title="평가 항목별 점수 레이더 차트",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True, key="radar_chart")
    
    with tab3:
        # 가중치 분석
        col1, col2 = st.columns(2)
        
        with col1:
            # 가중치 파이 차트
            weight_values = [weights.get(cat, 0) for cat in scores.keys()]
            
            fig = go.Figure(data=[go.Pie(
                labels=categories,
                values=weight_values,
                hole=0.3
            )])
            
            fig.update_layout(
                title="평가 항목별 가중치 분포",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True, key="pie_chart")
        
        with col2:
            # 가중치 효과 분석
            st.write("**가중치 효과 분석**")
            
            for cat in scores.keys():
                original = scores[cat]
                weighted = weighted_scores.get(cat, 0)
                weight = weights.get(cat, 0)
                effect = weighted - original
                
                st.write(f"**{category_names.get(cat, cat)}**")
                st.write(f"- 가중치: {weight:.3f}")
                st.write(f"- 효과: {effect:+.2f}")
                
                if effect > 0:
                    st.success("↗️ 점수 상승")
                elif effect < 0:
                    st.error("↘️ 점수 하락")
                else:
                    st.info("→ 변화 없음")
                st.write("---")
    
    st.markdown("---")
    
    # 상세 점수 표
    st.subheader("📋 상세 점수 표")
    
    if not PANDAS_AVAILABLE:
        st.error("상세 점수 표를 위해 Pandas가 필요합니다.")
        return
    
    df = pd.DataFrame({
        '평가 항목': [category_names.get(cat, cat) for cat in scores.keys()],
        '원본 점수': [f"{scores[cat]:.2f}" for cat in scores.keys()],
        '가중치': [f"{weights.get(cat, 0):.3f}" for cat in scores.keys()],
        '가중치 적용 점수': [f"{weighted_scores.get(cat, 0):.2f}" for cat in scores.keys()],
        '순위': range(1, len(scores) + 1)
    })
    
    # 원본 점수 기준으로 정렬
    df = df.sort_values('원본 점수', ascending=False).reset_index(drop=True)
    df['순위'] = range(1, len(df) + 1)
    
    st.dataframe(df, use_container_width=True)
    
    st.markdown("---")
    
    # 프로젝트 분류 및 가중치 정보
    st.subheader("🏷️ 프로젝트 분류 및 가중치 적용")
    
    classification = results.get('classification', {})
    if classification:
        col1, col2 = st.columns(2)
        
        with col1:
            # 분류 결과 시각화
            project_type = classification.get('project_type', 'Unknown').upper()
            confidence = classification.get('confidence', 0)
            painkiller_score = classification.get('painkiller_score', 0)
            vitamin_score = classification.get('vitamin_score', 0)
            
            # 분류 신뢰도 게이지 차트
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = confidence * 100,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': f"분류 신뢰도 ({project_type})"},
                delta = {'reference': 70},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"},
                        {'range': [80, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True, key="confidence_gauge")
            
            # PainKiller vs Vitamin 점수 비교
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=['PainKiller', 'Vitamin'],
                y=[painkiller_score, vitamin_score],
                marker_color=['red', 'green']
            ))
            
            fig2.update_layout(
                title='PainKiller vs Vitamin 점수',
                yaxis_title='점수',
                height=300
            )
            
            st.plotly_chart(fig2, use_container_width=True, key="painkiller_vitamin_chart")
        
        with col2:
            st.write("**분류 정보:**")
            st.info(f"""
            **프로젝트 유형:** {project_type}
            **분류 신뢰도:** {confidence:.1%}
            **PainKiller 점수:** {painkiller_score:.3f}
            **Vitamin 점수:** {vitamin_score:.3f}
            """)
            
            st.write("**분류 근거:**")
            st.write(classification.get('reasoning', '분류 근거가 없습니다.'))
            
            # 가중치 요약 정보
            weight_summary = results.get('weight_summary', '')
            if weight_summary:
                st.write("**적용된 가중치 정보:**")
                st.code(weight_summary, language='text')
    
    st.markdown("---")
    
    # 평가 체인별 상세 정보
    st.subheader("🔍 평가 체인별 상세 정보")
    
    evaluation_results = results.get('evaluation_results', {})
    
    if evaluation_results:
        # 각 평가 항목을 확장 가능한 섹션으로 표시
        for category, result in evaluation_results.items():
            if not isinstance(result, dict):
                continue
            
            category_name = category_names.get(category, category)
            score = result.get('score', result.get('total_score', 0))
            
            with st.expander(f"📋 {category_name} (점수: {score:.2f}/10)"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # 점수 표시
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = score,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "점수"},
                        gauge = {
                            'axis': {'range': [None, 10]},
                            'bar': {'color': "green"},
                            'steps': [
                                {'range': [0, 10], 'color': "lightgray"},
                            ]
                        }
                    ))
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True, key=f"gauge_chart_{category}")
                    
                    # 실행 시간
                    execution_time = result.get('execution_time', 0)
                    if execution_time:
                        st.metric("실행 시간", f"{execution_time:.3f}초")
                
                with col2:
                    # 평가 근거
                    reasoning = result.get('reasoning', '')
                    if reasoning:
                        st.write("**평가 근거:**")
                        st.write(reasoning)
                    
                    # 개선 제안
                    suggestions = result.get('suggestions', [])
                    if suggestions:
                        st.write("**개선 제안:**")
                        for i, suggestion in enumerate(suggestions[:3], 1):  # 최대 3개만 표시
                            st.write(f"{i}. {suggestion}")
                    
                    # 데이터 제한사항
                    limitations = result.get('data_limitations', '')
                    if limitations:
                        st.warning(f"**데이터 제한사항:** {limitations}")
                    
                    # 오류 정보
                    error = result.get('error', '')
                    if error:
                        st.error(f"**오류:** {error}")
    
    st.markdown("---")

if __name__ == "__main__":
    main()