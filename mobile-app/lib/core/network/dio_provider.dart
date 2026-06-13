import 'package:dio/dio.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'token_interceptor.dart';
import 'retry_interceptor.dart';

final secureStorageProvider = Provider<FlutterSecureStorage>((ref) {
  return const FlutterSecureStorage();
});

Dio _createDio(
  FlutterSecureStorage secureStorage, {
  Duration? receiveTimeout,
  bool enableRetry = true,
}) {
  final dio = Dio();
  final baseUrl = dotenv.env['API_BASE_URL'] ?? 'https://your-api-gateway.com';
  dio.options.baseUrl = baseUrl;
  dio.options.connectTimeout = const Duration(seconds: 15);
  dio.options.receiveTimeout = receiveTimeout ?? const Duration(seconds: 15);

  dio.interceptors.add(TokenInterceptor(secureStorage: secureStorage));
  if (enableRetry) {
    dio.interceptors.add(RetryInterceptor(dio: dio, maxRetries: 3));
  }

  return dio;
}

final dioProvider = Provider<Dio>((ref) {
  return _createDio(ref.watch(secureStorageProvider));
});

/// Long-polling client: JWT attached, no retry interceptor, extended receive timeout.
final longPollDioProvider = Provider<Dio>((ref) {
  return _createDio(
    ref.watch(secureStorageProvider),
    receiveTimeout: const Duration(seconds: 70),
    enableRetry: false,
  );
});
