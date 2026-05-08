# pages/01_📊_ماسحة_الأسهم.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def render_screener_interface():
    """واجهة ماسحة الأسهم"""
    
    st.header("🔍 ماسحة الأسهم المصرية - تصفية ذكية")
    
    # عمودين: معايير التصفية + النتائج
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("⚙️ معايير التصفية")
        
        # معايير سعرية
        with st.expander("💰 المعايير السعرية", expanded=True):
            price_min = st.number_input("الحد الأدنى للسعر", min_value=0, value=0)
            price_max = st.number_input("الحد الأقصى للسعر", min_value=0, value=1000)
            change_min = st.slider("نسبة التغير الدنيا (%)", -20, 20, -5)
            change_max = st.slider("نسبة التغير القصوى (%)", -20, 20, 5)
        
        # معايير مالية
        with st.expander("📊 المعايير المالية"):
            pe_min = st.number_input("مكرر الربحية الأدنى", min_value=0, value=0)
            pe_max = st.number_input("مكرر الربحية الأقصى", min_value=0, value=30)
            eps_min = st.number_input("ربحية السهم الأدنى", min_value=-10, value=0)
            growth_min = st.slider("نمو الإيرادات الأدنى (%)", -50, 100, 0)
        
        # معايير المخاطرة
        with st.expander("⚠️ المعايير الفنية"):
            beta_max = st.slider("معامل بيتا الأقصى", 0.0, 3.0, 2.0, 0.1)
            rsi_min = st.slider("RSI الأدنى", 0, 100, 30)
            rsi_max = st.slider("RSI الأقصى", 0, 100, 70)
        
        # معايير التوزيعات
        with st.expander("💰 توزيعات الأرباح"):
            dividend_min = st.slider("عائد التوزيعات الأدنى (%)", 0, 20, 3)
            show_dividend_only = st.checkbox("عرض الأسهم ذات التوزيعات فقط")
        
        # زر التصفية
        st.markdown("---")
        filter_button = st.button("🔍 تطبيق التصفية", type="primary", use_container_width=True)
    
    with col2:
        st.subheader("📈 نتائج التصفية")
        
        if filter_button:
            # محاكاة النتائج (سيتم استبدالها ببيانات حقيقية)
            results = filter_stocks(
                price_min=price_min, price_max=price_max,
                pe_min=pe_min, pe_max=pe_max,
                eps_min=eps_min, growth_min=growth_min,
                beta_max=beta_max, rsi_min=rsi_min, rsi_max=rsi_max,
                dividend_min=dividend_min if show_dividend_only else 0
            )
            
            if results:
                st.success(f"✅ تم العثور على {len(results)} سهماً")
                
                # عرض الجدول
                st.dataframe(
                    results,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "symbol": "الرمز",
                        "name": "الشركة",
                        "price": st.column_config.NumberColumn("السعر", format="%.2f"),
                        "change": st.column_config.NumberColumn("التغير %", format="%.2f%%"),
                        "pe": st.column_config.NumberColumn("P/E", format="%.1f"),
                        "dividend": st.column_config.NumberColumn("العائد %", format="%.2f%%"),
                        "rsi": st.column_config.NumberColumn("RSI", format="%.0f"),
                        "beta": st.column_config.NumberColumn("بيتا", format="%.2f")
                    }
                )
                
                # رسم بياني للنتائج
                fig = px.scatter(
                    results, x="pe", y="dividend",
                    size="market_cap", color="change",
                    hover_data=["name", "price"],
                    title="تحليل العائد مقابل المخاطرة",
                    labels={"pe": "مكرر الربحية", "dividend": "عائد التوزيعات (%)"}
                )
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.warning("⚠️ لا توجد أسهم تطابق المعايير المحددة")
        else:
            st.info("👈 اختر معايير التصفية من القائمة الجانبية")

def filter_stocks(**criteria):
    """دالة تصفية الأسهم بناءً على المعايير"""
    # سيتم ربطها بقاعدة البيانات الفعلية
    # حالياً بيانات تجريبية
    return []
