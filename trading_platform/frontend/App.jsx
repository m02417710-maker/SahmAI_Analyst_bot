/*
ملف: frontend/App.jsx
المسار: /trading_platform/frontend/App.jsx
الوظيفة: واجهة المستخدم الرئيسية - لوحة التحكم
*/

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart, Line, CandlestickChart, Candlestick,
  XAxis, YAxis, Tooltip, ResponsiveContainer
} from 'recharts';

const API_URL = 'http://localhost:8000/api';

function App() {
  const [selectedStock, setSelectedStock] = useState('COMI.CA');
  const [stockData, setStockData] = useState(null);
  const [indicators, setIndicators] = useState(null);
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(false);

  // جلب بيانات السهم
  const fetchStockData = async (symbol) => {
    setLoading(true);
    try {
      const [dataResponse, indicatorsResponse] = await Promise.all([
        axios.get(`${API_URL}/stock/${symbol}/data`),
        axios.get(`${API_URL}/stock/${symbol}/indicators`)
      ]);
      
      setStockData(dataResponse.data);
      setIndicators(indicatorsResponse.data);
    } catch (error) {
      console.error('خطأ في جلب البيانات:', error);
    }
    setLoading(false);
  };

  // جلب فرص الاستثمار
  const fetchOpportunities = async () => {
    try {
      const response = await axios.get(`${API_URL}/market/opportunities`);
      setOpportunities(response.data);
    } catch (error) {
      console.error('خطأ في جلب الفرص:', error);
    }
  };

  useEffect(() => {
    fetchStockData(selectedStock);
    fetchOpportunities();
    
    // تحديث كل 30 ثانية
    const interval = setInterval(() => {
      fetchStockData(selectedStock);
    }, 30000);
    
    return () => clearInterval(interval);
  }, [selectedStock]);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* شريط التنقل */}
      <nav className="bg-gray-800 p-4 shadow-lg">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-green-400">
            📈 منصة التحليل الاستثماري
          </h1>
          <div className="flex gap-4">
            <button className="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600">
              لوحة التحكم
            </button>
            <button className="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600">
              المحفظة
            </button>
            <button className="px-4 py-2 bg-gray-700 rounded hover:bg-gray-600">
              التقارير
            </button>
          </div>
        </div>
      </nav>

      <div className="container mx-auto p-6">
        {/* اختيار السهم */}
        <div className="mb-6">
          <label className="block text-sm mb-2">اختر السهم:</label>
          <select
            value={selectedStock}
            onChange={(e) => setSelectedStock(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 w-64"
          >
            <option value="COMI.CA">🇪🇬 CIB - البنك التجاري الدولي</option>
            <option value="TMGH.CA">🇪🇬 TMGH - طلعت مصطفى</option>
            <option value="2222.SR">🇸🇦 أرامكو السعودية</option>
            <option value="AAPL">🇺🇸 Apple Inc.</option>
            <option value="MSFT">🇺🇸 Microsoft Corp.</option>
          </select>
        </div>

        {/* بطاقات المؤشرات */}
        {indicators && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-gray-400 text-sm">السعر الحالي</div>
              <div className="text-2xl font-bold">
                {stockData?.price?.toFixed(2) || '---'}
              </div>
              <div className={`text-sm ${stockData?.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {stockData?.change >= 0 ? '▲' : '▼'} {Math.abs(stockData?.change_percent || 0).toFixed(2)}%
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-gray-400 text-sm">مؤشر RSI</div>
              <div className="text-2xl font-bold">{indicators.rsi?.toFixed(1) || '---'}</div>
              <div className="text-xs text-gray-400">
                {indicators.rsi > 70 ? 'ذروة شراء' : indicators.rsi < 30 ? 'ذروة بيع' : 'محايد'}
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-gray-400 text-sm">المتوسط 20</div>
              <div className="text-2xl font-bold">{indicators.sma_20?.toFixed(2) || '---'}</div>
            </div>

            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-gray-400 text-sm">حجم التداول</div>
              <div className="text-2xl font-bold">
                {indicators.volume_ratio?.toFixed(1) || '---'}x
              </div>
              <div className="text-xs text-gray-400">نسبة للمتوسط</div>
            </div>
          </div>
        )}

        {/* الرسم البياني */}
        <div className="bg-gray-800 rounded-lg p-4 mb-6">
          <h2 className="text-xl font-bold mb-4">📊 الرسم البياني</h2>
          <div className="h-96">
            {stockData?.chart_data && (
              <ResponsiveContainer width="100%" height="100%">
                <CandlestickChart data={stockData.chart_data}>
                  <XAxis dataKey="date" stroke="#888" />
                  <YAxis stroke="#888" domain={['auto', 'auto']} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: 'none' }}
                    labelStyle={{ color: '#fff' }}
                  />
                  <Candlestick
                    dataKey="ohlc"
                    upColor="#10b981"
                    downColor="#ef4444"
                  />
                </CandlestickChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* فرص الاستثمار */}
        <div className="bg-gray-800 rounded-lg p-4">
          <h2 className="text-xl font-bold mb-4">🎯 فرص الاستثمار اليوم</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-2">السهم</th>
                  <th className="text-left py-2">السعر</th>
                  <th className="text-left py-2">العائد</th>
                  <th className="text-left py-2">التوصية</th>
                  <th className="text-left py-2">المخاطرة</th>
                </tr>
              </thead>
              <tbody>
                {opportunities.map((opp, idx) => (
                  <tr key={idx} className="border-b border-gray-700">
                    <td className="py-2">{opp.name}</td>
                    <td className="py-2">{opp.current_price?.toFixed(2)}</td>
                    <td className={`py-2 ${opp.upside_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {opp.upside_percent >= 0 ? '+' : ''}{opp.upside_percent?.toFixed(1)}%
                    </td>
                    <td className="py-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        opp.action === 'strong_buy' ? 'bg-green-600' :
                        opp.action === 'buy' ? 'bg-green-800' :
                        opp.action === 'hold' ? 'bg-yellow-600' :
                        opp.action === 'sell' ? 'bg-orange-600' : 'bg-red-600'
                      }`}>
                        {opp.action === 'strong_buy' ? 'شراء قوي' :
                         opp.action === 'buy' ? 'شراء' :
                         opp.action === 'hold' ? 'انتظار' :
                         opp.action === 'sell' ? 'بيع' : 'بيع قوي'}
                      </span>
                    </td>
                    <td className="py-2">
                      <span className={`px-2 py-1 rounded text-xs ${
                        opp.risk_level === 'low' ? 'bg-green-600' :
                        opp.risk_level === 'medium' ? 'bg-yellow-600' : 'bg-red-600'
                      }`}>
                        {opp.risk_level === 'low' ? 'منخفضة' :
                         opp.risk_level === 'medium' ? 'متوسطة' : 'مرتفعة'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
