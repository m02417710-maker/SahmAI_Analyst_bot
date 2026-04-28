# -stock---ai--analyst-arabic-stock-analysis-bot-
 بوت تحليل الأسهم الذكي باستخدام Streamlit + yfinance + Google Gemini (يدعم الأسهم السعودية والعالمية)
# داخل Sidebar، بعد إعدادات السهم الواحد
st.divider()
st.subheader("🔄 مقارنة بين سهمين")

compare_mode = st.checkbox("تفعيل وضع المقارنة")
if compare_mode:
    ticker2 = st.text_input("رمز السهم الثاني", value="AAPL", help="مثال: AAPL أو TSLA أو 1180.SR")
    compare_period = st.selectbox("فترة المقارنة", options=["3mo", "6mo", "1y", "2y"], index=2)
    # ====================== مقارنة بين سهمين ======================
if compare_mode and ticker2:
    with st.spinner(f"جاري جلب بيانات المقارنة بين {ticker} و {ticker2}..."):
        hist1, info1 = get_stock_data(ticker, compare_period)
        hist2, info2 = get_stock_data(ticker2, compare_period)
    
    if hist1 is not None and hist2 is not None:
        # توحيد التواريخ للمقارنة
        compare_df = pd.DataFrame({
            ticker: hist1['Close'],
            ticker2: hist2['Close']
        }).dropna()
        
        # رسم مقارنة
        fig_compare = go.Figure()
        fig_compare.add_trace(go.Scatter(x=compare_df.index, y=compare_df[ticker], name=ticker, line=dict(width=3)))
        fig_compare.add_trace(go.Scatter(x=compare_df.index, y=compare_df[ticker2], name=ticker2, line=dict(width=3)))
        
        fig_compare.update_layout(
            title=f"مقارنة أداء {ticker} مقابل {ticker2}",
            height=500,
            template="plotly_dark",
            xaxis_title="التاريخ",
            yaxis_title="سعر الإغلاق"
        )
        st.plotly_chart(fig_compare, use_container_width=True)
        
        # تحليل المقارنة بـ Gemini
        if st.button("🔍 احصل على تحليل مقارن بـ Gemini", type="primary"):
            with st.spinner("جاري تحليل المقارنة..."):
                try:
                    prompt_compare = f"""
                    أنت محلل أسهم محترف. قارن بين السهمين التاليين باللغة العربية:

                    السهم الأول: {ticker} - {info1.get('longName', '')}
                    السهم الثاني: {ticker2} - {info2.get('longName', '')}

                    بيانات الأداء التاريخي (آخر 10 أيام):
                    {compare_df.tail(10).to_string()}

                    أعطِ مقارنة واضحة تشمل:
                    - الأداء النسبي
                    - التقلب (Volatility)
                    - نقاط القوة والضعف لكل سهم
                    - أي سهم أفضل حالياً ولماذا
                    - توصية استثمارية
                    """

                    response = model.generate_content(prompt_compare)
                    st.markdown("### 📊 تحليل المقارنة الذكي")
                    st.write(response.text)
                except Exception as e:
                    st.error(f"خطأ في تحليل المقارنة: {e}")
                    # 📈 بوت تحليل الأسهم الذكي - Stock AI Analyst

**واجهة ويب تفاعلية عربية** تجمع بين **بيانات البورصة الحية** و**الذكاء الاصطناعي** لتحليل الأسهم السعودية والعالمية.

![Stock Analysis Dashboard](https://via.placeholder.com/800x400/0A2540/00FFAA?text=Stock+AI+Analyst+Dashboard)  
*(استبدل برابط صورة شاشة حقيقية بعد التشغيل)*

---

## ✨ المميزات الرئيسية

- جلب بيانات حية من yfinance (دعم كامل لأسهم **تداول** مثل 2222.SR و1180.SR)
- رسوم بيانية احترافية تفاعلية (شموع + Bollinger Bands + Moving Averages)
- مؤشرات فنية متقدمة باستخدام **pandas_ta** (RSI, MACD, Bollinger Bands)
- **شات ذكي باللغة العربية** مدعوم بـ Google Gemini (Flash + Pro)
- **مقارنة بين سهمين** مع رسم وتحليل ذكي
- تحميل البيانات كملف CSV
- واجهة سريعة ومتجاوبة مبنية بـ **Streamlit**

---

## 🛠️ التقنيات المستخدمة

| التقنية              | الاستخدام                          |
|----------------------|------------------------------------|
| **Streamlit**        | واجهة الويب التفاعلية            |
| **yfinance**         | جلب البيانات الحية                |
| **pandas_ta**        | حساب المؤشرات الفنية              |
| **Google Gemini**    | التحليل الذكي والردود بالعربية   |
| **Plotly**           | رسوم بيانية عالية الجودة          |
| **Pandas**           | معالجة البيانات                    |

---

## 🚀 كيفية التشغيل محلياً

```bash
git clone https://github.com/اسم_مستخدمك/stock-ai-analyst.git
cd stock-ai-analyst

# تثبيت المكتبات
pip install -r requirements.txt

# تشغيل التطبيق
streamlit run app.py
