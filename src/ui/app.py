"""
Streamlit UI for AgenticTravelRAG
사용자 친화적인 여행 계획 인터페이스 (Updated for Google Gemini & UI Improvements)
"""

import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python Path에 추가
sys.path.append(str(Path(__file__).parent.parent.parent))

# 페이지 설정
st.set_page_config(
    page_title="🌍 AgenticTravelRAG",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API 서버 URL
API_URL = os.getenv("API_URL", "http://localhost:8000")

# 세션 상태 초기화
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_plan' not in st.session_state:
    st.session_state.current_plan = None

# CSS 스타일
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1e88e5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
        font-size: 1.1rem;
    }
    .hotel-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 5px solid #1e88e5;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .weather-card {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        text-align: center;
        border: 1px solid #bbdefb;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .weather-date {
        font-weight: bold;
        font-size: 1.1rem;
        color: #1565c0;
        margin-bottom: 0.3rem;
    }
    .weather-desc {
        color: #424242;
        font-size: 0.95rem;
        margin-bottom: 0.3rem;
    }
    .weather-temp {
        color: #d32f2f;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .highlight-tag {
        background-color: #e1f5fe;
        color: #0277bd;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.85rem;
        margin-right: 0.3rem;
    }
</style>
""", unsafe_allow_html=True)

# 헤더
st.markdown('<h1 class="main-header">🌍 AgenticTravelRAG</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Google Gemini & TripAdvisor 리뷰 기반 지능형 여행 플래너</p>', unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.header("🎯 여행 설정")
    
    # API 연결 상태
    st.markdown("### 🔌 시스템 상태")
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            health = response.json()
            if health['status'] == 'healthy':
                st.success("✅ 시스템 정상 작동 중")
            else:
                st.warning("⚠️ 일부 기능 제한")
            
            col1, col2 = st.columns(2)
            with col1:
                if health['elasticsearch']:
                    st.caption("ElasticSearch: 🟢")
                else:
                    st.caption("ElasticSearch: 🔴")
            with col2:
                if health['workflow']:
                    st.caption("Workflow: 🟢")
                else:
                    st.caption("Workflow: 🔴")
    except:
        st.error("❌ API 서버 연결 실패")
    
    st.markdown("---")
    
    # 예시 쿼리
    st.markdown("### 💡 예시 질문")
    example_queries = [
        "12월 20일부터 3일간 파리에서 묵을 조용하고 낭만적인 호텔 추천해줘",
        "방콕 여행 가는데 수영장 있고 조식 맛있는 호텔 찾아줘. 날짜는 다음주.",
        "서울 강남 근처 비즈니스 호텔, 10만원대",
        "뉴욕 가족 여행, 아이들과 가기 좋은 숙소 추천"
    ]
    
    for query in example_queries:
        if st.button(query, key=f"ex_{query[:5]}"):
            st.session_state.input_query = query
    
    st.markdown("---")
    
    # 세션 관리
    st.markdown("### 📝 대화 세션")
    if st.session_state.session_id:
        st.info(f"Session: {st.session_state.session_id[:8]}...")
        if st.button("🔄 새 대화 시작"):
            st.session_state.session_id = None
            st.session_state.chat_history = []
            st.session_state.current_plan = None
            if 'input_query' in st.session_state:
                del st.session_state.input_query
            st.rerun()
    else:
        st.info("새 대화를 시작하세요")

# 메인 영역
col1, col2 = st.columns([1.8, 1.2])

with col1:
    st.header("💬 여행 상담")
    
    # 채팅 인터페이스
    chat_container = st.container()
    
    # 입력 폼
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "여행 계획을 물어보세요:",
            value=st.session_state.get('input_query', ''),
            height=100,
            placeholder="예: 12월 25일부터 3박 4일, 파리에서 낭만적인 호텔 추천해줘. 예산은 1박에 30만원 정도."
        )
        
        col_submit, col_clear = st.columns([1, 5])
        with col_submit:
            submit_button = st.form_submit_button("🚀 전송", use_container_width=True)
        with col_clear:
            if st.form_submit_button("🗑️ 지우기"):
                st.session_state.chat_history = []
                st.session_state.current_plan = None
    
    # 쿼리 처리
    if submit_button and user_input:
        # 사용자 메시지 추가
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # API 호출
        with st.spinner("🤖 여행 정보를 분석하고 계획을 생성 중입니다..."):
            try:
                response = requests.post(
                    f"{API_URL}/api/v1/plan",
                    json={
                        "query": user_input,
                        "session_id": st.session_state.session_id
                    },
                    timeout=120  # LLM 처리 시간 고려하여 넉넉하게
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result['success']:
                        st.session_state.session_id = result['session_id']
                        st.session_state.current_plan = result
                        
                        # AI 응답 추가
                        response_text = ""
                        if result.get('itinerary'):
                            response_text = result['itinerary'].get('summary', '여행 계획이 생성되었습니다.')
                        else:
                            response_text = "죄송합니다. 계획 생성 중 오류가 발생했습니다."
                        
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response_text,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        st.rerun() # 화면 갱신
                    else:
                        st.error(f"오류: {result.get('error', '알 수 없는 오류')}")
                else:
                    st.error(f"API 오류: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                st.error("⏱️ 요청 시간이 초과되었습니다. 다시 시도해주세요.")
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
    
    # 대화 히스토리 표시
    with chat_container:
        if not st.session_state.chat_history:
            st.info("여행에 대해 무엇이든 물어보세요! AI가 리뷰 데이터와 날씨 정보를 바탕으로 답변해드립니다.")
        
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                with st.chat_message("user", avatar="👤"):
                    st.write(msg['content'])
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(msg['content'])

with col2:
    st.header("📊 상세 정보")
    
    if st.session_state.current_plan:
        plan = st.session_state.current_plan
        
        # 호텔 정보
        hotels = plan.get('hotels', [])
        if hotels:
            st.subheader(f"🏨 추천 호텔 ({len(hotels)})")
            for hotel in hotels[:3]:
                # 필드명 호환성 처리 (price vs price_range)
                price = hotel.get('price_range') or hotel.get('price') or '정보 없음'
                
                with st.expander(f"**{hotel.get('name', 'Unknown')}** ⭐ {hotel.get('rating', 'N/A')}", expanded=True):
                    st.markdown(f"**📍 위치:** {hotel.get('location', 'N/A')}")
                    st.markdown(f"**💰 가격대:** {price}")
                    
                    highlights = hotel.get('highlights') or hotel.get('review_highlights')
                    if highlights:
                        st.markdown("**✨ 리뷰 하이라이트:**")
                        for highlight in highlights:
                            st.markdown(f"- {highlight}")
        elif plan.get('itinerary'):
             st.info("검색된 호텔이 없습니다.")

        # 날씨 정보 (가독성 개선)
        weather = plan.get('weather', [])
        if weather:
            st.subheader("☀️ 날씨 예보")
            
            cols = st.columns(2)
            for idx, forecast in enumerate(weather[:4]):
                date = forecast.get('date', 'N/A')
                desc = forecast.get('description', 'N/A')
                temp_min = forecast.get('temperature_min', 0)
                temp_max = forecast.get('temperature_max', 0)
                
                with cols[idx % 2]:
                    st.markdown(f"""
                    <div class="weather-card">
                        <div class="weather-date">{date}</div>
                        <div class="weather-desc">{desc}</div>
                        <div class="weather-temp">{temp_min}°C ~ {temp_max}°C</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # 디버그 정보 (실행 경로 시각화)
        st.markdown("---")
        with st.expander("🔍 실행 경로 (Workflow Debug)", expanded=False):
            if plan.get('execution_path'):
                st.caption("에이전트 실행 순서:")
                path_str = " → ".join([f"**{node}**" for node in plan['execution_path']])
                st.markdown(path_str)
            else:
                st.caption("실행 경로 정보가 없습니다.")

# 하단 정보
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🔧 기술 스택")
    st.write("• LangGraph Multi-Agent")
    st.write("• ElasticSearch (Vector Search)")
    st.write("• TripAdvisor Reviews Data")

with col2:
    st.markdown("### 🌐 외부 API")
    st.write("• Google Gemini 2.5 (Flash/Pro)")
    st.write("• Open-Meteo (Weather)")
    st.write("• SerpApi (Google Search)")

with col3:
    st.markdown("### 🚀 주요 기능")
    st.write("• 한국어 쿼리 자동 번역 검색")
    st.write("• 날씨 기반 일정 추천")
    st.write("• 리뷰 기반 감성 분석")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888; padding: 20px;'>
        <p>AgenticTravelRAG - Powered by LangGraph & Google Gemini</p>
        <p>Make your trip perfect with AI Agent</p>
    </div>
    """,
    unsafe_allow_html=True
)
