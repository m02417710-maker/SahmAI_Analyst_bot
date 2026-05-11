"""
محلل الأسهم المتقدم - مكتبة المؤشرات الفنية
Advanced Stock Analyzer - Technical Indicators Library
Version: 2.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import json


class TechnicalIndicators:
    """فئة شاملة لحساب المؤشرات الفنية"""
    
    def __init__(self, historical_data: pd.DataFrame):
        """
        تهيئة فئة المؤشرات الفنية
        
        Args:
            historical_data: DataFrame يحتوي على أعمدة:
                           ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        """
        self.data = historical_data.copy()
        self.data = self.data.sort_values('Date').reset_index(drop=True)
        self.indicators = {}
    
    # ============================================================
    # المتوسطات المتحركة (Moving Averages)
    # ============================================================
    
    def calculate_sma(self, period: int = 20, column: str = 'Close') -> pd.Series:
        """
        حساب المتوسط المتحرك البسيط
        Simple Moving Average (SMA)
        """
        sma = self.data[column].rolling(window=period).mean()
        self.indicators[f'SMA_{period}'] = sma
        return sma
    
    def calculate_ema(self, period: int = 12, column: str = 'Close') -> pd.Series:
        """
        حساب المتوسط المتحرك الأسي
        Exponential Moving Average (EMA)
        """
        ema = self.data[column].ewm(span=period, adjust=False).mean()
        self.indicators[f'EMA_{period}'] = ema
        return ema
    
    def calculate_wma(self, period: int = 20, column: str = 'Close') -> pd.Series:
        """
        حساب المتوسط المتحرك الموزون
        Weighted Moving Average (WMA)
        """
        weights = np.arange(1, period + 1)
        wma = self.data[column].rolling(window=period).apply(
            lambda x: np.sum(x * weights) / np.sum(weights), raw=False
        )
        self.indicators[f'WMA_{period}'] = wma
        return wma
    
    # ============================================================
    # مؤشر القوة النسبية (RSI)
    # ============================================================
    
    def calculate_rsi(self, period: int = 14, column: str = 'Close') -> pd.Series:
        """
        حساب مؤشر القوة النسبية
        Relative Strength Index (RSI)
        
        القيم:
        - 0-30: منطقة بيع زائد (Oversold)
        - 30-70: منطقة محايدة (Neutral)
        - 70-100: منطقة شراء زائد (Overbought)
        """
        delta = self.data[column].diff()
        
        # الأرباح والخسائر
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # المتوسطات المتحركة للأرباح والخسائر
        avg_gains = gains.rolling(window=period).mean()
        avg_losses = losses.rolling(window=period).mean()
        
        # حساب RS و RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        self.indicators['RSI'] = rsi
        return rsi
    
    # ============================================================
    # مؤشر MACD
    # ============================================================
    
    def calculate_macd(self, 
                      fast: int = 12, 
                      slow: int = 26, 
                      signal: int = 9,
                      column: str = 'Close') -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        حساب مؤشر MACD
        Moving Average Convergence Divergence
        
        Returns:
            (macd_line, signal_line, histogram)
        """
        ema_fast = self.data[column].ewm(span=fast, adjust=False).mean()
        ema_slow = self.data[column].ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        self.indicators['MACD'] = macd_line
        self.indicators['MACD_Signal'] = signal_line
        self.indicators['MACD_Histogram'] = histogram
        
        return macd_line, signal_line, histogram
    
    # ============================================================
    # نطاقات بولينجر (Bollinger Bands)
    # ============================================================
    
    def calculate_bollinger_bands(self, 
                                  period: int = 20, 
                                  std_dev: float = 2.0,
                                  column: str = 'Close') -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        حساب نطاقات بولينجر
        Bollinger Bands
        
        Returns:
            (upper_band, middle_band, lower_band)
        """
        middle = self.data[column].rolling(window=period).mean()
        std = self.data[column].rolling(window=period).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        self.indicators['BB_Upper'] = upper
        self.indicators['BB_Middle'] = middle
        self.indicators['BB_Lower'] = lower
        
        return upper, middle, lower
    
    # ============================================================
    # مؤشر الحجم (Volume Indicators)
    # ============================================================
    
    def calculate_obv(self, column: str = 'Volume') -> pd.Series:
        """
        حساب مؤشر الحجم على التوازن
        On-Balance Volume (OBV)
        """
        obv = pd.Series(0.0, index=self.data.index)
        obv.iloc[0] = 0
        
        for i in range(1, len(self.data)):
            if self.data['Close'].iloc[i] > self.data['Close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + self.data[column].iloc[i]
            elif self.data['Close'].iloc[i] < self.data['Close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - self.data[column].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        self.indicators['OBV'] = obv
        return obv
    
    def calculate_adl(self) -> pd.Series:
        """
        حساب خط التراكم/التوزيع
        Accumulation/Distribution Line
        """
        clv = ((self.data['Close'] - self.data['Low']) - 
               (self.data['High'] - self.data['Close'])) / (
               self.data['High'] - self.data['Low'])
        
        adl = (clv * self.data['Volume']).cumsum()
        
        self.indicators['ADL'] = adl
        return adl
    
    # ============================================================
    # مؤشرات الزخم (Momentum Indicators)
    # ============================================================
    
    def calculate_roc(self, period: int = 12, column: str = 'Close') -> pd.Series:
        """
        حساب معدل التغيير
        Rate of Change (ROC)
        """
        roc = ((self.data[column] - self.data[column].shift(period)) / 
               self.data[column].shift(period)) * 100
        
        self.indicators[f'ROC_{period}'] = roc
        return roc
    
    def calculate_momentum(self, period: int = 12, column: str = 'Close') -> pd.Series:
        """
        حساب الزخم
        Momentum = Price - Price n periods ago
        """
        momentum = self.data[column] - self.data[column].shift(period)
        
        self.indicators[f'Momentum_{period}'] = momentum
        return momentum
    
    def calculate_stochastic(self, 
                            k_period: int = 14, 
                            d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """
        حساب مؤشر ستوكاستيك
        Stochastic Oscillator
        
        Returns:
            (%K, %D)
        """
        low_min = self.data['Low'].rolling(window=k_period).min()
        high_max = self.data['High'].rolling(window=k_period).max()
        
        k_percent = 100 * ((self.data['Close'] - low_min) / 
                           (high_max - low_min))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        self.indicators['Stochastic_K'] = k_percent
        self.indicators['Stochastic_D'] = d_percent
        
        return k_percent, d_percent
    
    # ============================================================
    # مؤشرات التذبذب (Volatility Indicators)
    # ============================================================
    
    def calculate_atr(self, period: int = 14) -> pd.Series:
        """
        حساب مؤشر النطاق الحقيقي المتوسط
        Average True Range (ATR)
        """
        high_low = self.data['High'] - self.data['Low']
        high_close = abs(self.data['High'] - self.data['Close'].shift())
        low_close = abs(self.data['Low'] - self.data['Close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(period).mean()
        
        self.indicators['ATR'] = atr
        return atr
    
    # ============================================================
    # المؤشرات الأساسية (Fundamental Indicators)
    # ============================================================
    
    def calculate_fundamental_metrics(self,
                                     current_price: float,
                                     pe_ratio: float,
                                     earnings_per_share: float,
                                     dividend_per_share: float,
                                     book_value: float,
                                     debt_to_equity: float) -> Dict:
        """
        حساب المؤشرات الأساسية
        """
        pb_ratio = current_price / book_value if book_value > 0 else 0
        dividend_yield = (dividend_per_share / current_price) * 100 if current_price > 0 else 0
        
        metrics = {
            'PE_Ratio': pe_ratio,
            'EPS': earnings_per_share,
            'PB_Ratio': pb_ratio,
            'Dividend_Yield': dividend_yield,
            'Debt_to_Equity': debt_to_equity,
            'Book_Value': book_value
        }
        
        self.indicators.update(metrics)
        return metrics
    
    # ============================================================
    # نظام الإشارات الذكي
    # ============================================================
    
    def generate_signals(self) -> Dict:
        """
        توليد إشارات التداول بناءً على جميع المؤشرات
        """
        signals = {
            'buy_signals': [],
            'sell_signals': [],
            'neutral_signals': [],
            'strength': 0,
            'recommendation': 'HOLD',
            'confidence': 0
        }
        
        latest_data = self.data.iloc[-1]
        
        # فحص المتوسطات المتحركة
        if 'SMA_20' in self.indicators and 'SMA_50' in self.indicators:
            sma20 = self.indicators['SMA_20'].iloc[-1]
            sma50 = self.indicators['SMA_50'].iloc[-1]
            
            if sma20 > sma50:
                signals['buy_signals'].append('SMA_20 > SMA_50 (Uptrend)')
                signals['strength'] += 2
            elif sma20 < sma50:
                signals['sell_signals'].append('SMA_20 < SMA_50 (Downtrend)')
                signals['strength'] -= 2
        
        # فحص RSI
        if 'RSI' in self.indicators:
            rsi = self.indicators['RSI'].iloc[-1]
            if rsi < 30:
                signals['buy_signals'].append('RSI < 30 (Oversold)')
                signals['strength'] += 1
            elif rsi > 70:
                signals['sell_signals'].append('RSI > 70 (Overbought)')
                signals['strength'] -= 1
        
        # فحص MACD
        if 'MACD' in self.indicators and 'MACD_Signal' in self.indicators:
            macd = self.indicators['MACD'].iloc[-1]
            signal = self.indicators['MACD_Signal'].iloc[-1]
            
            if macd > signal:
                signals['buy_signals'].append('MACD > Signal (Bullish)')
                signals['strength'] += 2
            elif macd < signal:
                signals['sell_signals'].append('MACD < Signal (Bearish)')
                signals['strength'] -= 2
        
        # تحديد التوصية
        if signals['strength'] >= 3:
            signals['recommendation'] = 'BUY'
            signals['confidence'] = min(100, 70 + signals['strength'] * 5)
        elif signals['strength'] <= -3:
            signals['recommendation'] = 'SELL'
            signals['confidence'] = min(100, 70 + abs(signals['strength']) * 5)
        else:
            signals['recommendation'] = 'HOLD'
            signals['confidence'] = 50
        
        return signals
    
    # ============================================================
    # حساب النقاط الإجمالية
    # ============================================================
    
    def calculate_overall_score(self,
                               fundamentals: Dict,
                               technicals_signals: Dict) -> Dict:
        """
        حساب النقاط الإجمالية للسهم
        """
        score = 50  # نقطة البداية
        
        # النقاط الأساسية (50%)
        if fundamentals.get('PE_Ratio', 999) < 15:
            score += 10
        
        if fundamentals.get('Dividend_Yield', 0) > 3:
            score += 10
        
        if fundamentals.get('Debt_to_Equity', 999) < 0.5:
            score += 10
        
        # النقاط الفنية (50%)
        score += technicals_signals['strength'] * 5
        
        # تقييم نهائي
        rating = 'WEAK'
        if score >= 80:
            rating = 'EXCELLENT'
        elif score >= 70:
            rating = 'GOOD'
        elif score >= 60:
            rating = 'FAIR'
        elif score >= 50:
            rating = 'NEUTRAL'
        else:
            rating = 'WEAK'
        
        return {
            'total_score': min(100, max(0, score)),
            'rating': rating,
            'technical_strength': technicals_signals['strength'],
            'fundamental_strength': (score - 50) * 0.5,
            'recommendation': technicals_signals['recommendation']
        }
    
    # ============================================================
    # التصدير والتقارير
    # ============================================================
    
    def get_all_indicators(self) -> Dict:
        """الحصول على جميع المؤشرات المحسوبة"""
        result = {}
        for key, value in self.indicators.items():
            if isinstance(value, pd.Series):
                result[key] = value.iloc[-1] if len(value) > 0 else None
            else:
                result[key] = value
        return result
    
    def generate_report(self) -> str:
        """توليد تقرير نصي شامل"""
        report = []
        report.append("=" * 60)
        report.append("تقرير المؤشرات الفنية الشامل")
        report.append(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 60)
        
        for indicator, value in self.get_all_indicators().items():
            if isinstance(value, (int, float)):
                report.append(f"{indicator}: {value:.4f}")
            else:
                report.append(f"{indicator}: {value}")
        
        report.append("=" * 60)
        return "\n".join(report)


# ============================================================
# فئة تحليل المحفظة
# ============================================================

class PortfolioAnalyzer:
    """فئة لتحليل المحفظة الاستثمارية"""
    
    def __init__(self, portfolio: Dict[str, Dict]):
        """
        portfolio = {
            'TELECOM': {'quantity': 100, 'purchase_price': 16.5, 'current_price': 18.5},
            ...
        }
        """
        self.portfolio = portfolio
    
    def calculate_portfolio_value(self) -> Dict:
        """حساب قيمة المحفظة"""
        total_investment = 0
        total_value = 0
        total_gain = 0
        
        for stock, data in self.portfolio.items():
            investment = data['quantity'] * data['purchase_price']
            current = data['quantity'] * data['current_price']
            gain = current - investment
            
            total_investment += investment
            total_value += current
            total_gain += gain
        
        return {
            'total_investment': total_investment,
            'total_value': total_value,
            'total_gain': total_gain,
            'total_return_percent': (total_gain / total_investment * 100) if total_investment > 0 else 0
        }
    
    def calculate_allocation(self) -> Dict:
        """حساب توزيع المحفظة"""
        total = sum(data['quantity'] * data['current_price'] 
                   for data in self.portfolio.values())
        
        allocation = {}
        for stock, data in self.portfolio.items():
            value = data['quantity'] * data['current_price']
            allocation[stock] = (value / total * 100) if total > 0 else 0
        
        return allocation


# ============================================================
# مثال على الاستخدام
# ============================================================

if __name__ == "__main__":
    # إنشاء بيانات تاريخية وهمية
    dates = pd.date_range(start='2024-01-01', periods=100)
    np.random.seed(42)
    
    closes = np.cumsum(np.random.randn(100)) + 100
    highs = closes + np.abs(np.random.randn(100))
    lows = closes - np.abs(np.random.randn(100))
    opens = closes + np.random.randn(100) * 0.5
    volumes = np.random.randint(1000000, 5000000, 100)
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': closes,
        'Volume': volumes
    })
    
    # حساب المؤشرات
    analyzer = TechnicalIndicators(df)
    
    analyzer.calculate_sma(20)
    analyzer.calculate_sma(50)
    analyzer.calculate_ema(12)
    analyzer.calculate_rsi()
    analyzer.calculate_macd()
    analyzer.calculate_bollinger_bands()
    analyzer.calculate_atr()
    
    # طباعة التقرير
    print(analyzer.generate_report())
    
    # الحصول على الإشارات
    signals = analyzer.generate_signals()
    print("\n" + "=" * 60)
    print("إشارات التداول")
    print("=" * 60)
    print(f"التوصية: {signals['recommendation']}")
    print(f"درجة الثقة: {signals['confidence']}%")
    print(f"إشارات الشراء: {signals['buy_signals']}")
    print(f"إشارات البيع: {signals['sell_signals']}")
