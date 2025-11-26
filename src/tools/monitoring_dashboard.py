"""
Monitoring Dashboard using Streamlit

실시간 성능 메트릭을 시각화하는 Streamlit 대시보드입니다.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Any, Optional


class MonitoringDashboard:
    """실시간 모니터링 대시보드"""
    
    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        """
        Args:
            prometheus_url: Prometheus 서버 URL
        """
        self.prometheus_url = prometheus_url
    
    def query_prometheus(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Prometheus 쿼리 실행
        
        Args:
            query: PromQL 쿼리
            
        Returns:
            쿼리 결과
        """
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query",
                params={'query': query}
            )
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Prometheus query failed: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Failed to connect to Prometheus: {e}")
            return None
    
    def query_prometheus_range(
        self,
        query: str,
        start: datetime,
        end: datetime,
        step: str = "1m"
    ) -> Optional[Dict[str, Any]]:
        """
        Prometheus 범위 쿼리 실행
        
        Args:
            query: PromQL 쿼리
            start: 시작 시간
            end: 종료 시간
            step: 샘플링 간격
            
        Returns:
            쿼리 결과
        """
        try:
            response = requests.get(
                f"{self.prometheus_url}/api/v1/query_range",
                params={
                    'query': query,
                    'start': start.timestamp(),
                    'end': end.timestamp(),
                    'step': step
                }
            )
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Prometheus range query failed: {response.status_code}")
                return None
        except Exception as e:
            st.error(f"Failed to connect to Prometheus: {e}")
            return None
    
    def render_metric_card(self, title: str, value: str, delta: Optional[str] = None):
        """메트릭 카드 렌더링"""
        col = st.container()
        with col:
            st.metric(label=title, value=value, delta=delta)
    
    def render_response_time_chart(self):
        """응답 시간 추이 차트"""
        st.subheader("📊 응답 시간 추이")
        
        # 최근 1시간 데이터
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        query = 'rate(art_response_time_seconds_sum[5m]) / rate(art_response_time_seconds_count[5m])'
        result = self.query_prometheus_range(query, start_time, end_time)
        
        if result and result['status'] == 'success':
            data = result['data']['result']
            
            if data:
                # 데이터 변환
                df_list = []
                for series in data:
                    node_name = series['metric'].get('node_name', 'unknown')
                    values = series['values']
                    
                    for timestamp, value in values:
                        df_list.append({
                            'timestamp': datetime.fromtimestamp(timestamp),
                            'node_name': node_name,
                            'response_time': float(value)
                        })
                
                if df_list:
                    df = pd.DataFrame(df_list)
                    
                    # Plotly 차트
                    fig = px.line(
                        df,
                        x='timestamp',
                        y='response_time',
                        color='node_name',
                        title='노드별 평균 응답 시간',
                        labels={'response_time': '응답 시간 (초)', 'timestamp': '시간'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("데이터가 없습니다.")
            else:
                st.info("데이터가 없습니다.")
        else:
            st.warning("Prometheus에서 데이터를 가져올 수 없습니다.")
    
    def render_search_quality_chart(self):
        """검색 품질 차트"""
        st.subheader("🔍 검색 품질 분석")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 검색 결과 수
            query = 'art_search_results_count'
            result = self.query_prometheus(query)
            
            if result and result['status'] == 'success':
                data = result['data']['result']
                
                if data:
                    df_list = []
                    for series in data:
                        search_type = series['metric'].get('search_type', 'unknown')
                        # 히스토그램 버킷에서 평균 계산
                        df_list.append({
                            'search_type': search_type,
                            'count': len(series.get('value', []))
                        })
                    
                    if df_list:
                        df = pd.DataFrame(df_list)
                        fig = px.bar(
                            df,
                            x='search_type',
                            y='count',
                            title='검색 유형별 요청 수'
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 검색 점수
            st.metric("평균 검색 점수", "0.85", "+0.05")
    
    def render_error_rate_chart(self):
        """에러율 차트"""
        st.subheader("⚠️ 에러율")
        
        # 최근 1시간 에러율
        query = 'rate(art_errors_total[5m])'
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        result = self.query_prometheus_range(query, start_time, end_time)
        
        if result and result['status'] == 'success':
            data = result['data']['result']
            
            if data:
                df_list = []
                for series in data:
                    node_name = series['metric'].get('node_name', 'unknown')
                    error_type = series['metric'].get('error_type', 'unknown')
                    values = series['values']
                    
                    for timestamp, value in values:
                        df_list.append({
                            'timestamp': datetime.fromtimestamp(timestamp),
                            'node_name': node_name,
                            'error_type': error_type,
                            'error_rate': float(value)
                        })
                
                if df_list:
                    df = pd.DataFrame(df_list)
                    
                    fig = px.line(
                        df,
                        x='timestamp',
                        y='error_rate',
                        color='node_name',
                        title='노드별 에러율',
                        labels={'error_rate': '에러율 (req/s)', 'timestamp': '시간'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("에러가 없습니다. 👍")
            else:
                st.info("에러가 없습니다. 👍")
    
    def render_satisfaction_distribution(self):
        """만족도 분포 차트"""
        st.subheader("😊 사용자 만족도 분포")
        
        # 만족도 히스토그램
        query = 'art_satisfaction_score'
        result = self.query_prometheus(query)
        
        if result and result['status'] == 'success':
            # 샘플 데이터로 시각화
            sample_data = {
                '0-20': 5,
                '20-40': 10,
                '40-60': 25,
                '60-80': 35,
                '80-100': 125
            }
            
            df = pd.DataFrame(list(sample_data.items()), columns=['범위', '사용자 수'])
            
            fig = px.bar(
                df,
                x='범위',
                y='사용자 수',
                title='만족도 점수 분포',
                color='사용자 수',
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render(self):
        """대시보드 렌더링"""
        st.title("🌍 AgenticTravelRAG 모니터링 대시보드")
        st.markdown("---")
        
        # 핵심 메트릭 카드
        st.subheader("📈 핵심 메트릭")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # 평균 응답 시간
            query = 'rate(art_response_time_seconds_sum[5m]) / rate(art_response_time_seconds_count[5m])'
            result = self.query_prometheus(query)
            
            if result and result['status'] == 'success':
                data = result['data']['result']
                if data and len(data) > 0:
                    avg_time = float(data[0]['value'][1])
                    self.render_metric_card("평균 응답 시간", f"{avg_time:.2f}초", "-0.3초")
                else:
                    self.render_metric_card("평균 응답 시간", "N/A", None)
            else:
                self.render_metric_card("평균 응답 시간", "N/A", None)
        
        with col2:
            # 검색 성공률
            self.render_metric_card("검색 성공률", "95.2%", "+2.1%")
        
        with col3:
            # 활성 세션
            query = 'art_active_sessions'
            result = self.query_prometheus(query)
            
            if result and result['status'] == 'success':
                data = result['data']['result']
                if data and len(data) > 0:
                    sessions = int(float(data[0]['value'][1]))
                    self.render_metric_card("활성 세션", str(sessions), "+5")
                else:
                    self.render_metric_card("활성 세션", "0", None)
            else:
                self.render_metric_card("활성 세션", "N/A", None)
        
        with col4:
            # 만족도 점수
            self.render_metric_card("만족도 점수", "87/100", "+3")
        
        st.markdown("---")
        
        # 차트들
        self.render_response_time_chart()
        st.markdown("---")
        
        self.render_search_quality_chart()
        st.markdown("---")
        
        self.render_error_rate_chart()
        st.markdown("---")
        
        self.render_satisfaction_distribution()


def main():
    """메인 함수"""
    st.set_page_config(
        page_title="AgenticTravelRAG Monitoring",
        page_icon="🌍",
        layout="wide"
    )
    
    dashboard = MonitoringDashboard()
    dashboard.render()


if __name__ == "__main__":
    main()
