// ملف: mobile/lib/screens/subscription_screen.dart
// المسار: /trading_platform/mobile/lib/screens/subscription_screen.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/subscription_provider.dart';
import '../widgets/plan_card.dart';

class SubscriptionScreen extends StatelessWidget {
  const SubscriptionScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final subscriptionProvider = Provider.of<SubscriptionProvider>(context);
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('الاشتراكات'),
        backgroundColor: Colors.green,
      ),
      body: subscriptionProvider.isLoading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // الاشتراك الحالي
                if (subscriptionProvider.currentSubscription != null)
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [Colors.green, Colors.teal],
                      ),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'اشتراكك الحالي',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 10),
                        Text(
                          subscriptionProvider.currentSubscription!.plan.name,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 5),
                        Text(
                          'ينتهي في: ${_formatDate(subscriptionProvider.currentSubscription!.endDate)}',
                          style: const TextStyle(color: Colors.white70),
                        ),
                        const SizedBox(height: 10),
                        if (subscriptionProvider.currentSubscription!.autoRenew)
                          const Chip(
                            label: Text('تجديد تلقائي مفعل'),
                            backgroundColor: Colors.white,
                            labelStyle: TextStyle(color: Colors.green),
                          ),
                      ],
                    ),
                  ),
                
                const SizedBox(height: 20),
                
                // قائمة الخطط
                const Text(
                  'اختر الخطة المناسبة لك',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 10),
                
                ...subscriptionProvider.plans.map((plan) {
                  final isCurrent = subscriptionProvider.currentSubscription?.plan.type == plan.type;
                  return PlanCard(
                    plan: plan,
                    isCurrent: isCurrent,
                    onSelect: () => _showSubscribeDialog(context, plan),
                  );
                }).toList(),
                
                const SizedBox(height: 20),
                
                // معلومات الضمان
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.grey[800],
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    children: [
                      const Icon(Icons.security, size: 40, color: Colors.green),
                      const SizedBox(height: 10),
                      const Text(
                        'دفع آمن 100%',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      const SizedBox(height: 5),
                      Text(
                        'نستخدم بوابات دفع مشفرة لحماية معلوماتك',
                        style: TextStyle(color: Colors.grey[400]),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
  
  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }
  
  void _showSubscribeDialog(BuildContext context, Plan plan) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(plan.name),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('السعر الشهري: ${plan.priceMonthly} ج.م'),
            const SizedBox(height: 10),
            Text('السعر السنوي: ${plan.priceYearly} ج.م (وفر ${((plan.priceMonthly * 12 - plan.priceYearly) / (plan.priceMonthly * 12) * 100).toInt()}%)'),
            const SizedBox(height: 10),
            const Text('المميزات:'),
            ...plan.features.entries.where((e) => e.value).map((feature) {
              return Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    const Icon(Icons.check_circle, size: 16, color: Colors.green),
                    const SizedBox(width: 8),
                    Text(_getFeatureName(feature.key)),
                  ],
                ),
              );
            }).toList(),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('إلغاء'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              final success = await context.read<SubscriptionProvider>().subscribe(plan.type);
              if (success) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('تم الاشتراك بنجاح!')),
                );
              } else {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('حدث خطأ، حاول مرة أخرى')),
                );
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
            child: const Text('اشتراك الآن'),
          ),
        ],
      ),
    );
  }
  
  String _getFeatureName(String key) {
    const names = {
      'stock_analysis': 'تحليل الأسهم',
      'realtime_data': 'بيانات لحظية',
      'ai_analysis': 'تحليل بالذكاء الاصطناعي',
      'auto_trading': 'تداول آلي',
      'telegram_bot': 'بوت تليجرام',
      'portfolio_tracking': 'متابعة المحفظة',
      'alerts': 'تنبيهات ذكية',
      'api_access': 'API للتكامل',
    };
    return names[key] ?? key;
  }
}
