"""
Streamlit UI for AgenticTravelRAG
사용자 친화적인 여행 계획 인터페이스
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
        margin-bottom: 2rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .hotel-card {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .weather-card {
        background-color: #e3f2fd;
        padding: 0.8rem;
        border-radius: 8px;
        margin: 0.3rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 헤더
st.markdown('<h1 class="main-header">🌍 AgenticTravelRAG</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">TripAdvisor 리뷰 기반 지능형 여행 플래너 - 당신만의 완벽한 여행을 설계하세요</p>', unsafe_allow_html=True)

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
                    st.success("ES ✓")
                else:
                    st.error("ES ✗")
            with col2:
                if health['workflow']:
                    st.success("WF ✓")
                else:
                    st.error("WF ✗")
    except:
        st.error("❌ API 서버 연결 실패")
    
    st.markdown("---")
    
    # 예시 쿼리
    st.markdown("### 💡 예시 질문")
    example_queries = [
        "방콕에서 조용하고 평점 높은 호텔 추천해줘",
        "12월 파리 신혼여행, 낭만적인 호텔 찾아줘",
        "도쿄 3박4일 가족여행 계획 짜줘",
        "바르셀로나 맛집 근처 호텔 추천"
    ]
    
    for query in example_queries:
        if st.button(query, key=f"ex_{query[:10]}"):
            st.session_state.input_query = query
    
    st.markdown("---")
    
    # 세션 관리
    st.markdown("### 📝 대화 세션")
    if st.session_state.session_id:
        st.info(f"세션 ID: {st.session_state.session_id[:8]}...")
        if st.button("🔄 새 대화 시작"):
            st.session_state.session_id = None
            st.session_state.chat_history = []
            st.session_state.current_plan = None
            st.rerun()
    else:
        st.info("새 대화를 시작하세요")

# 메인 영역
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 대화")
    
    # 채팅 인터페이스
    chat_container = st.container()
    
    # 입력 폼
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "여행에 대해 무엇이든 물어보세요:",
            value=st.session_state.get('input_query', ''),
            height=100,
            placeholder="예: 12월에 파리 여행 가는데, 에펠탑 근처에 조용하고 아늑한 호텔 추천해줘. 2명이 3박 할 예정이야."
        )
        
        col_submit, col_clear = st.columns([1, 5])
        with col_submit:
            submit_button = st.form_submit_button("🚀 전송", use_container_width=True)
        with col_clear:
            if st.form_submit_button("🗑️ 초기화"):
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
        with st.spinner("🤔 여행 계획을 생성하고 있습니다..."):
            try:
                response = requests.post(
                    f"{API_URL}/api/v1/plan",
                    json={
                        "query": user_input,
                        "session_id": st.session_state.session_id
                    },
                    timeout=60
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
                        
                        st.success("✅ 여행 계획이 생성되었습니다!")
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
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                st.chat_message("user").write(msg['content'])
            else:
                st.chat_message("assistant").write(msg['content'])

with col2:
    st.header("📊 여행 정보")
    
    if st.session_state.current_plan:
        plan = st.session_state.current_plan
        
        # 호텔 정보
        if plan.get('hotels'):
            st.subheader("🏨 추천 호텔")
            for hotel in plan['hotels'][:3]:
                with st.expander(f"**{hotel.get('name', 'Unknown')}** ⭐ {hotel.get('rating', 'N/A')}"):
                    st.write(f"📍 위치: {hotel.get('location', 'N/A')}")
                    st.write(f"💰 가격대: {hotel.get('price', 'N/A')}")
                    if hotel.get('highlights'):
                        st.write("✨ 특징:")
                        for highlight in hotel['highlights']:
                            st.write(f"  • {highlight}")
        
        # 날씨 정보
        if plan.get('weather'):
            st.subheader("☀️ 날씨 예보")
            for forecast in plan['weather'][:5]:
                date = forecast.get('date', 'N/A')
                desc = forecast.get('description', 'N/A')
                temp_min = forecast.get('temperature_min', 0)
                temp_max = forecast.get('temperature_max', 0)
                
                st.markdown(f"""
                <div class="weather-card">
                    <b>{date}</b><br>
                    {desc}<br>
                    🌡️ {temp_min}°C ~ {temp_max}°C
                </div>
                """, unsafe_allow_html=True)

# 하단 정보
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🔧 기술 스택")
    st.write("• LangGraph Multi-Agent")
    st.write("• ElasticSearch RAG")
    st.write("• TripAdvisor Reviews")

with col2:
    st.markdown("### 🌐 외부 API")
    st.write("• Open-Meteo (날씨)")
    st.write("• SerpApi (구글 검색)")
    st.write("• OpenAI GPT")

with col3:
    st.markdown("### 📚 데이터 소스")
    st.write("• 20,000+ 리뷰")
    st.write("• 실시간 날씨")
    st.write("• 하이브리드 검색")

# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888;'>
        <p>AgenticTravelRAG - Powered by LangGraph & ElasticSearch</p>
        <p>TripAdvisor 리뷰 데이터 기반 지능형 여행 플래너</p>
    </div>
    """,
    unsafe_allow_html=True
)

# 디버그 모드
if st.checkbox("🔍 디버그 모드", value=False):
    st.markdown("### Debug Information")
    st.json({
        "session_id": st.session_state.session_id,
        "chat_history_length": len(st.session_state.chat_history),
        "has_current_plan": bool(st.session_state.current_plan),
        "api_url": API_URL
    })
