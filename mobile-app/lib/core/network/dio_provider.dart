import 'package:dio/dio.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'token_interceptor.dart';
import 'retry_interceptor.dart';

final secureStorageProvider = Provider<FlutterSecureStorage>((ref) {
  return const FlutterSecureStorage();
});

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio();

  // Set base URL from dotenv
  final baseUrl = dotenv.env['API_BASE_URL'] ?? 'https://your-api-gateway.com';
  dio.options.baseUrl = baseUrl;
  
  // Set default timeouts
  dio.options.connectTimeout = const Duration(seconds: 15);
  dio.options.receiveTimeout = const Duration(seconds: 15);

  final secureStorage = ref.watch(secureStorageProvider);

  dio.interceptors.addAll([
    TokenInterceptor(secureStorage: secureStorage),
    RetryInterceptor(dio: dio, maxRetries: 3), // Exactly 3 attempts
  ]);

  return dio;
});
