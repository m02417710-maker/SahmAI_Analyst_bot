/*
ملف: frontend/src/App.jsx
المسار: /trading_platform/frontend/src/App.jsx
الوظيفة: واجهة المستخدم الرئيسية - لوحة التحكم المتقدمة
*/

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  LineChart, Line, CandlestickChart, Candlestick,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart
} from 'recharts';
import { Bell, TrendingUp, TrendingDown, DollarSign, Users, BookOpen, Trophy } from 'lucide-react';

// ====================== إعدادات ======================
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// ====================== المكون الرئيسي ======================
function App() {
  const [selectedStock, setSelectedStock] = useState('COMI.CA');
  const [stockData, setStockData] = useState(null);
  const [indicators, setIndicators] = useState(null);
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [darkMode, setDarkMode] = useState(true);
  const [notifications, setNotifications] = useState([]);

  // ====================== جلب البيانات ======================
  const fetchStockData = async (symbol) => {
    setLoading(true);
    try {
      const [dataResponse, indicatorsResponse] = await Promise.all([
        axios.get(`${API_URL}/stock/${symbol}`),
        axios.get(`${API_URL}/indicators/${symbol}`)
      ]);
      
      setStockData(dataResponse.data);
      setIndicators(indicatorsResponse.data);
    } catch (error) {
      console.error('خطأ في جلب البيانات:', error);
      addNotification('خطأ في جلب بيانات السهم', 'error');
    }
    setLoading(false);
  };

  const fetchOpportunities = async () => {
    try {
      const response = await axios.get(`${API_URL}/market/opportunities`);
      setOpportunities(response.data.opportunities || []);
    } catch (error) {
      console.error('خطأ في جلب الفرص:', error);
    }
  };

  const addNotification = (message, type = 'info') => {
    const newNotification = {
      id: Date.now(),
      message,
      type,
      timestamp: new Date()
    };
    setNotifications(prev => [newNotification, ...prev].slice(0, 10));
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== newNotification.id));
    }, 5000);
  };

  useEffect(() => {
    fetchStockData(selectedStock);
    fetchOpportunities();
    
    const interval = setInterval(() => {
      fetchStockData(selectedStock);
    }, 30000);
    
    return () => clearInterval(interval);
  }, [selectedStock]);

  // ====================== إشارات التداول ======================
  const getSignalColor = (action) => {
    switch(action) {
      case 'strong_buy': return 'bg-green-600';
      case 'buy': return 'bg-green-800';
      case 'hold': return 'bg-yellow-600';
      case 'sell': return 'bg-orange-600';
      case 'strong_sell': return 'bg-red-600';
      default: return 'bg-gray-600';
    }
  };

  const getSignalText = (action) => {
    switch(action) {
      case 'strong_buy': return 'شراء قوي';
      case 'buy': return 'شراء';
      case 'hold': return 'انتظار';
      case 'sell': return 'بيع';
      case 'strong_sell': return 'بيع قوي';
      default: return 'غير محدد';
    }
  };

  // ====================== الـ JSX ======================
  return (
    <div className={`min-h-screen ${darkMode ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-900'}`}>
      {/* شريط التنقل */}
      <nav className={`${darkMode ? 'bg-gray-800' : 'bg-white shadow-lg'} p-4 sticky top-0 z-50`}>
        <div className="container mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-3 rtl:space-x-reverse">
            <div className="text-2xl">📈</div>
            <h1 className="text-2xl font-bold text-green-500">منصة التداول الذكية</h1>
            <span className="text-xs bg-green-500 text-white px-2 py-1 rounded">BETA</span>
          </div>
          
          <div className="flex items-center space-x-4 rtl:space-x-reverse">
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg hover:bg-gray-700 transition"
            >
              {darkMode ? '☀️' : '🌙'}
            </button>
            
            <div className="relative">
              <Bell className="w-5 h-5 cursor-pointer" />
              {notifications.length > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                  {notifications.length}
                </span>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* الإشعارات */}
      {notifications.length > 0 && (
        <div className="fixed top-20 right-4 z-50 space-y-2">
          {notifications.map(notif => (
            <div key={notif.id} className={`p-3 rounded-lg shadow-lg ${
              notif.type === 'error' ? 'bg-red-500' : 'bg-green-500'
            } text-white animate-slide-in`}>
              {notif.message}
            </div>
          ))}
        </div>
      )}

      <div className="container mx-auto p-6">
        {/* بطاقات المؤشرات */}
        {indicators && stockData && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
            <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg p-4 shadow-lg`}>
              <div className="text-gray-400 text-sm">السعر الحالي</div>
              <div className="text-2xl font-bold">{stockData.price?.toFixed(2) || '---'}</div>
              <div className={`text-sm ${stockData.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {stockData.change >= 0 ? '▲' : '▼'} {Math.abs(stockData.change_percent || 0).toFixed(2)}%
              </div>
            </div>

            <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg p-4 shadow-lg`}>
              <div className="text-gray-400 text-sm">مؤشر RSI</div>
              <div className="text-2xl font-bold">{indicators.rsi?.toFixed(1) || '---'}</div>
              <div className="text-xs text-gray-400">
                {indicators.rsi > 70 ? '🔴 ذروة شراء' : indicators.rsi < 30 ? '🟢 ذروة بيع' : '⚪ محايد'}
              </div>
            </div>

            <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg p-4 shadow-lg`}>
              <div className="text-gray-400 text-sm">المتوسط 20</div>
              <div className="text-2xl font-bold">{indicators.sma_20?.toFixed(2) || '---'}</div>
            </div>

            <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg p-4 shadow-lg`}>
              <div className="text-gray-400 text-sm">المتوسط 50</div>
              <div className="text-2xl font-bold">{indicators.sma_50?.toFixed(2) || '---'}</div>
            </div>

            <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg p-4 shadow-lg`}>
              <div className="text-gray-400 text-sm">حجم التداول</div>
              <div className="text-2xl font-bold">{indicators.volume_ratio?.toFixed(1) || '---'}x</div>
              <div className="text-xs text-gray-400">نسبة للمتوسط</div>
            </div>
          </div>
        )}

        {/* اختيار السهم */}
        <div className="mb-6">
          <label className="block text-sm mb-2">اختر السهم:</label>
          <select
            value={selectedStock}
            onChange={(e) => setSelectedStock(e.target.value)}
            className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-300'} border rounded-lg px-4 py-2 w-64`}
          >
            <option value="COMI.CA">🇪🇬 CIB - البنك التجاري الدولي</option>
            <option value="TMGH.CA">🇪🇬 TMGH - طلعت مصطفى</option>
            <option value="SWDY.CA">🇪🇬 SWDY - السويدي إليكتريك</option>
            <option value="2222.SR">🇸🇦 أرامكو السعودية</option>
            <option value="1120.SR">🇸🇦 مصرف الراجحي</option>
            <option value="AAPL">🇺🇸 Apple Inc.</option>
            <option value="MSFT">🇺🇸 Microsoft Corp.</option>
            <option value="TSLA">🇺🇸 Tesla Inc.</option>
            <option value="NVDA">🇺🇸 NVIDIA Corp.</option>
          </select>
        </div>

        {/* فرص الاستثمار */}
        {opportunities.length > 0 && (
          <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-lg p-4 mb-6 shadow-lg`}>
            <h2 className="text-xl font-bold mb-4 flex items-center">
              <Trophy className="w-5 h-5 mr-2 text-yellow-500" />
              فرص الاستثمار اليوم
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className={`border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                    <th className="text-right py-2">السهم</th>
                    <th className="text-right py-2">السعر</th>
                    <th className="text-right py-2">العائد</th>
                    <th className="text-right py-2">التوصية</th>
                    <th className="text-right py-2">المخاطرة</th>
                    <th className="text-right py-2">الثقة</th>
                  </tr>
                </thead>
                <tbody>
                  {opportunities.slice(0, 5).map((opp, idx) => (
                    <tr key={idx} className={`border-b ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
                      <td className="py-2 font-medium">{opp.name} <span className="text-xs text-gray-400">({opp.symbol})</span></td>
                      <td className="py-2">{opp.current_price?.toFixed(2)}</td>
                      <td className={`py-2 font-bold ${opp.upside_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {opp.upside_percent >= 0 ? '+' : ''}{opp.upside_percent?.toFixed(1)}%
                      </td>
                      <td className="py-2">
                        <span className={`px-2 py-1 rounded text-xs text-white ${getSignalColor(opp.action)}`}>
                          {getSignalText(opp.action)}
                        </span>
                      </td>
                      <td className="py-2">
                        <span className={`px-2 py-1 rounded text-xs ${
                          opp.risk_level === 'low' ? 'bg-green-600' :
                          opp.risk_level === 'medium' ? 'bg-yellow-600' : 'bg-red-600'
                        } text-white`}>
                          {opp.risk_level === 'low' ? 'منخفضة' : opp.risk_level === 'medium' ? 'متوسطة' : 'مرتفعة'}
                        </span>
                      </td>
                      <td className="py-2">
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-700 rounded-full h-2 mr-2">
                            <div className="bg-green-500 h-2 rounded-full" style={{ width: `${opp.confidence}%` }}></div>
                          </div>
                          <span className="text-xs">{opp.confidence}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* حالة التحميل */}
        {loading && (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
          </div>
        )}

        {/* رسالة عند عدم وجود بيانات */}
        {!loading && !stockData && (
          <div className="text-center py-12">
            <p className="text-gray-400">لا توجد بيانات متاحة</p>
          </div>
        )}
      </div>

      {/* تذييل الصفحة */}
      <footer className={`${darkMode ? 'bg-gray-800' : 'bg-gray-200'} p-4 mt-8 text-center text-sm text-gray-400`}>
        <p>© 2024 منصة التداول الذكية | البيانات من Yahoo Finance | التحليل بالذكاء الاصطناعي</p>
        <p className="text-xs mt-1">⚠️ للأغراض التعليمية فقط - ليست نصيحة استثمارية</p>
      </footer>

      {/* إضافة CSS للرسوم المتحركة */}
      <style jsx>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        .animate-slide-in {
          animation: slideIn 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}

export default App;
