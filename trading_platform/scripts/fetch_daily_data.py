#!/usr/bin/env python3
"""
ملف: scripts/fetch_daily_data.py
المسار: /trading_platform/scripts/fetch_daily_data.py
الوظيفة: جلب البيانات اليومية للأسهم
"""

import yfinance as yf
import pandas as pd
import json
from datetime import datetime, timedelta
import os
import sys

# قائمة الأسهم المصرية والسعودية والأمريكية
STOCKS = {
    "COMI.CA": "البنك التجاري الدولي",
    "TMGH.CA": "طلعت مصطفى القابضة",
    "SWDY.CA": "السويدي إليكتريك",
    "EAST.CA": "الشرقية للدخان",
    "2222.SR": "أرامكو السعودية",
    "1120.SR": "مصرف الراجحي",
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corp.",
    "TSLA": "Tesla Inc.",
}

def fetch_stock_data(symbol: str, period: str = "1mo"):
    """جلب بيانات السهم"""
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)
        
        if df.empty:
            return None
        
        # حساب المؤشرات الأساسية
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
        change = current_price - prev_price
        change_percent = (change / prev_price) * 100 if prev_price else 0
        
        return {
            "symbol": symbol,
            "name": STOCKS.get(symbol, symbol),
            "price": round(current_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "volume": int(df['Volume'].iloc[-1]),
            "high": round(df['High'].iloc[-1], 2),
            "low": round(df['Low'].iloc[-1], 2),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"خطأ في جلب {symbol}: {e}")
        return None

def main():
    """الدالة الرئيسية"""
    print(f"📊 بدء جلب البيانات - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    for symbol in STOCKS:
        print(f"  • جلب {symbol}...", end=" ")
        data = fetch_stock_data(symbol)
        if data:
            results.append(data)
            print(f"✅ {data['price']}")
        else:
            print("❌ فشل")
    
    # حفظ النتائج
    os.makedirs("data", exist_ok=True)
    with open("data/market_snapshot.json", "w", encoding="utf-8") as f:
        json.dump({
            "date": datetime.now().isoformat(),
            "stocks": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ تم حفظ {len(results)} سهم في data/market_snapshot.json")

if __name__ == "__main__":
    main()
