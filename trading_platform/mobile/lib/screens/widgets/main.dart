// ملف: mobile/lib/main.dart
// المسار: /trading_platform/mobile/lib/main.dart

import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'screens/splash_screen.dart';
import 'providers/stock_provider.dart';
import 'providers/auth_provider.dart';
import 'providers/portfolio_provider.dart';
import 'themes/app_theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // تهيئة Hive للتخزين المحلي
  await Hive.initFlutter();
  await Hive.openBox('settings');
  await Hive.openBox('favorites');
  
  runApp(const TradingPlatformApp());
}

class TradingPlatformApp extends StatelessWidget {
  const TradingPlatformApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => StockProvider()),
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => PortfolioProvider()),
      ],
      child: MaterialApp(
        title: 'منصة التداول',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.darkTheme,
        locale: const Locale('ar', 'EG'),
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: const [Locale('ar', 'EG')],
        home: const SplashScreen(),
      ),
    );
  }
}
