"""
ملف: backend/reports/tax_report.py
المسار: /trading_platform/backend/reports/tax_report.py
الوظيفة: توليد تقارير الضرائب والفواتير الرسمية
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import pdfkit
from jinja2 import Template
from loguru import logger

@dataclass
class TaxTransaction:
    """معاملة ضريبية"""
    transaction_id: str
    user_id: str
    date: datetime
    symbol: str
    transaction_type: str  # buy, sell, dividend
    quantity: int
    price: float
    total_amount: float
    fees: float
    tax_amount: float
    profit_loss: float
    notes: str = ""

@dataclass
class TaxReport:
    """تقرير ضريبي"""
    user_id: str
    username: str
    tax_year: int
    total_income: float
    total_expenses: float
    net_profit: float
    tax_due: float
    transactions: List[TaxTransaction]
    generated_date: datetime

class TaxReportGenerator:
    """مولد التقارير الضريبية"""
    
    def __init__(self, tax_rate: float = 0.225):  # 22.5% ضريبة أرباح رأسمالية في مصر
        self.tax_rate = tax_rate
        
    async def generate_annual_tax_report(self, user_id: str, year: int) -> TaxReport:
        """توليد تقرير ضريبي سنوي"""
        # جلب جميع معاملات المستخدم للسنة
        transactions = await self._get_user_transactions_for_year(user_id, year)
        
        if not transactions:
            return None
        
        # حساب الإجماليات
        total_income = sum(t.total_amount for t in transactions if t.transaction_type == "sell")
        total_expenses = sum(t.total_amount for t in transactions if t.transaction_type == "buy")
        total_fees = sum(t.fees for t in transactions)
        total_profit_loss = sum(t.profit_loss for t in transactions)
        
        net_profit = total_income - total_expenses - total_fees
        tax_due = net_profit * self.tax_rate if net_profit > 0 else 0
        
        # معلومات المستخدم
        user_info = await self._get_user_info(user_id)
        
        return TaxReport(
            user_id=user_id,
            username=user_info.get("username", user_id),
            tax_year=year,
            total_income=total_income,
            total_expenses=total_expenses,
            net_profit=net_profit,
            tax_due=tax_due,
            transactions=transactions,
            generated_date=datetime.now()
        )
    
    async def generate_monthly_tax_report(self, user_id: str, year: int, month: int) -> TaxReport:
        """توليد تقرير ضريبي شهري"""
        start_date = datetime(year, month, 1)
        end_date = start_date + timedelta(days=32)
        end_date = end_date.replace(day=1) - timedelta(days=1)
        
        transactions = await self._get_user_transactions_between(user_id, start_date, end_date)
        
        if not transactions:
            return None
        
        total_income = sum(t.total_amount for t in transactions if t.transaction_type == "sell")
        total_expenses = sum(t.total_amount for t in transactions if t.transaction_type == "buy")
        total_fees = sum(t.fees for t in transactions)
        
        net_profit = total_income - total_expenses - total_fees
        tax_due = net_profit * self.tax_rate if net_profit > 0 else 0
        
        user_info = await self._get_user_info(user_id)
        
        return TaxReport(
            user_id=user_id,
            username=user_info.get("username", user_id),
            tax_year=year,
            total_income=total_income,
            total_expenses=total_expenses,
            net_profit=net_profit,
            tax_due=tax_due,
            transactions=transactions,
            generated_date=datetime.now()
        )
    
    async def export_tax_report_to_pdf(self, tax_report: TaxReport) -> bytes:
        """تصدير التقرير الضريبي إلى PDF"""
        # قالب HTML للتقرير
        html_template = """
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>التقرير الضريبي - منصة التداول</title>
            <style>
                body {
                    font-family: 'Cairo', Arial, sans-serif;
                    line-height: 1.6;
                    margin: 40px;
                    color: #333;
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 2px solid #333;
                    padding-bottom: 20px;
                }
                .logo {
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c5f2d;
                }
                .report-title {
                    font-size: 20px;
                    margin-top: 10px;
                }
                .info-box {
                    background: #f5f5f5;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 5px;
                }
                .summary {
                    display: flex;
                    justify-content: space-between;
                    margin: 20px 0;
                }
                .summary-card {
                    background: #fff;
                    border: 1px solid #ddd;
                    padding: 15px;
                    border-radius: 5px;
                    width: 23%;
                    text-align: center;
                }
                .summary-card h3 {
                    margin: 0 0 10px 0;
                    font-size: 14px;
                    color: #666;
                }
                .summary-card .amount {
                    font-size: 20px;
                    font-weight: bold;
                    color: #2c5f2d;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: right;
                }
                th {
                    background-color: #2c5f2d;
                    color: white;
                }
                .footer {
                    text-align: center;
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                }
                .positive {
                    color: green;
                }
                .negative {
                    color: red;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="logo">🏦 منصة التداول الذكية</div>
                <div class="report-title">التقرير الضريبي السنوي {{ report.tax_year }}</div>
            </div>
            
            <div class="info-box">
                <p><strong>المستخدم:</strong> {{ report.username }} ({{ report.user_id }})</p>
                <p><strong>تاريخ التقرير:</strong> {{ report.generated_date.strftime('%Y-%m-%d %H:%M') }}</p>
                <p><strong>الفترة الضريبية:</strong> السنة المالية {{ report.tax_year }}</p>
            </div>
            
            <div class="summary">
                <div class="summary-card">
                    <h3>إجمالي الإيرادات</h3>
                    <div class="amount">{{ "%.2f"|format(report.total_income) }} ج.م</div>
                </div>
                <div class="summary-card">
                    <h3>إجمالي المصروفات</h3>
                    <div class="amount">{{ "%.2f"|format(report.total_expenses) }} ج.م</div>
                </div>
                <div class="summary-card">
                    <h3>صافي الربح</h3>
                    <div class="amount {{ 'positive' if report.net_profit > 0 else 'negative' }}">
                        {{ "%.2f"|format(report.net_profit) }} ج.م
                    </div>
                </div>
                <div class="summary-card">
                    <h3>الضريبة المستحقة</h3>
                    <div class="amount">{{ "%.2f"|format(report.tax_due) }} ج.م</div>
                </div>
            </div>
            
            <h3>تفاصيل المعاملات</h3>
            <table>
                <thead>
                    <tr>
                        <th>التاريخ</th>
                        <th>السهم</th>
                        <th>النوع</th>
                        <th>الكمية</th>
                        <th>السعر</th>
                        <th>الإجمالي</th>
                        <th>الربح/الخسارة</th>
                    </tr>
                </thead>
                <tbody>
                    {% for trans in report.transactions %}
                    <tr>
                        <td>{{ trans.date.strftime('%Y-%m-%d') }}</td>
                        <td>{{ trans.symbol }}</td>
                        <td>{{ 'شراء' if trans.transaction_type == 'buy' else 'بيع' }}</td>
                        <td>{{ trans.quantity }}</td>
                        <td>{{ "%.2f"|format(trans.price) }}</td>
                        <td>{{ "%.2f"|format(trans.total_amount) }}</td>
                        <td class="{{ 'positive' if trans.profit_loss > 0 else 'negative' }}">
                            {{ "%.2f"|format(trans.profit_loss) }}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            
            <div class="footer">
                <p>هذا التقرير تم إنشاؤه تلقائياً بواسطة منصة التداول الذكية</p>
                <p>يرجى الاحتفاظ بهذا التقرير للسجلات الضريبية الخاصة بك</p>
                <p>للأسئلة والاستفسارات: tax@trading-platform.com</p>
            </div>
        </body>
        </html>
        """
        
        template = Template(html_template)
        html_content = template.render(report=tax_report)
        
        # تحويل HTML إلى PDF
        pdf_bytes = pdfkit.from_string(html_content, False, options={
            'enable-local-file-access': None,
            'encoding': 'UTF-8'
        })
        
        return pdf_bytes
    
    async def _get_user_transactions_for_year(self, user_id: str, year: int) -> List[TaxTransaction]:
        """جلب معاملات المستخدم لسنة محددة"""
        # يمكن جلب من قاعدة البيانات
        # هنا بيانات تجريبية
        mock_transactions = []
        
        for i in range(5):
            profit_loss = (i + 1) * 1000 * (1 if i % 2 == 0 else -1)
            mock_transactions.append(
                TaxTransaction(
                    transaction_id=f"TX_{year}_{i}",
                    user_id=user_id,
                    date=datetime(year, i+1, 15),
                    symbol="COMI.CA" if i % 2 == 0 else "TMGH.CA",
                    transaction_type="sell" if i % 2 == 0 else "buy",
                    quantity=100,
                    price=50 + i * 10,
                    total_amount=(50 + i * 10) * 100,
                    fees=5.5,
                    tax_amount=0,
                    profit_loss=profit_loss
                )
            )
        
        return mock_transactions
    
    async def _get_user_transactions_between(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[TaxTransaction]:
        """جلب معاملات المستخدم بين تاريخين"""
        # تنفيذ مماثل للدالة أعلاه
        return []
    
    async def _get_user_info(self, user_id: str) -> Dict:
        """الحصول على معلومات المستخدم"""
        return {
            "username": f"user_{user_id}",
            "email": f"{user_id}@example.com",
            "tax_id": f"TAX_{user_id}",
            "address": "مصر"
        }
