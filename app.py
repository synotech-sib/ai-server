# ... (상단 import 및 스타일 설정 생략 - 기존 코드 유지) ...

# --- [5. Command Center (Step 8: 시각화 대시보드 강화)] ---
if st.session_state.get('admin_mode', False):
    st.markdown("---")
    st.header(f"🛡️ SynoCore Intelligence Dashboard")
    
    # 데이터 불러오기
    leads_df = get_leads()
    audit_df = get_audit_logs()
    
    # 상단 요약 지표 (KPI Metrics)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Leads", f"{len(leads_df)} 건")
    m2.metric("Total Simulations", f"{len(audit_df[audit_df['action'].str.contains('Run|Analysis', na=False)])} 회")
    m3.metric("System Uptime", "100%")
    m4.metric("Active Sessions", len(audit_df['user'].unique()))

    # 탭 구성 (통계 그래프 탭 추가)
    tab_chart, tab_log, tab_lead = st.tabs(["📈 Analytics View", "📜 Audit Logs", "📊 Partner Leads"])
    
    with tab_chart:
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("🏢 Partner Company Distribution")
            if not leads_df.empty:
                comp_counts = leads_df['company'].value_counts()
                st.bar_chart(comp_counts) # 간단한 막대 그래프
            else:
                st.info("데이터가 충분하지 않습니다.")
        
        with c2:
            st.subheader("⚡ Simulation Trends (Wh/kg)")
            # 감사 로그에서 시뮬레이션 결과값 추출 시도
            sim_logs = audit_df[audit_df['action'].str.contains('Wh/kg', na=False)]
            if not sim_logs.empty:
                # 'Run: 448.0 Wh/kg' 형태에서 숫자만 추출
                try:
                    sim_logs['energy_val'] = sim_logs['action'].str.extract(r'(\d+\.?\d*)').astype(float)
                    st.line_chart(sim_logs['energy_val']) # 시간에 따른 에너지 밀도 변화
                except:
                    st.write("데이터 형식을 변환할 수 없습니다.")
            else:
                st.info("시뮬레이션 기록이 없습니다.")

        st.divider()
        st.subheader("🕒 User Activity Heatmap")
        # 시간대별 활동량 분석 (예시)
        audit_df['timestamp'] = pd.to_datetime(audit_df['timestamp'])
        audit_df['hour'] = audit_df['timestamp'].dt.hour
        hour_counts = audit_df['hour'].value_counts().sort_index()
        st.area_chart(hour_counts)

    with tab_log:
        show_human = st.checkbox("Human Activity Only", value=True, key="admin_filter_human")
        display_df = audit_df[audit_df['user'] != 'System'] if show_human else audit_df
        st.dataframe(display_df, use_container_width=True)
        st.download_button("📥 Download Logs", display_df.to_csv(index=False).encode('utf-8-sig'), "synocore_audit.csv")
    
    with tab_lead:
        st.dataframe(leads_df, use_container_width=True)
        st.download_button("📥 Download Leads", leads_df.to_csv(index=False).encode('utf-8-sig'), "synocore_leads.csv")

# ... (하단 마감 코드 유지) ...