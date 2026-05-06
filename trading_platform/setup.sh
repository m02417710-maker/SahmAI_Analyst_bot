#!/bin/bash
# ملف: setup.sh
# المسار: /trading_platform/setup.sh

echo "🔧 تثبيت المتطلبات..."
pip install --upgrade pip
pip install streamlit yfinance pandas numpy plotly pandas-ta google-generativeai

echo "✅ تم تثبيت جميع المكتبات"
echo "🚀 تشغيل التطبيق..."
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
