import 'dart:math';
import 'package:dio/dio.dart';

class RetryInterceptor extends Interceptor {
  final Dio dio;
  final int maxRetries;
  static const String _retryCountKey = 'retry_count';

  RetryInterceptor({required this.dio, this.maxRetries = 3});

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final extra = err.requestOptions.extra;
    final retryCount = extra[_retryCountKey] ?? 0;

    if (_shouldRetry(err) && retryCount < maxRetries) {
      final nextRetryCount = retryCount + 1;
      
      // Exponential backoff: 2^retryCount * 1000 ms
      // e.g., 1s, 2s, 4s
      final delay = Duration(milliseconds: pow(2, retryCount).toInt() * 1000);
      
      await Future.delayed(delay);

      extra[_retryCountKey] = nextRetryCount;
      err.requestOptions.extra = extra;

      try {
        final response = await dio.fetch(err.requestOptions);
        return handler.resolve(response);
      } catch (e) {
        if (e is DioException) {
          return super.onError(e, handler);
        }
      }
    }

    return super.onError(err, handler);
  }

  bool _shouldRetry(DioException err) {
    // Retry on network errors and 5xx server errors
    return err.type == DioExceptionType.connectionTimeout ||
           err.type == DioExceptionType.sendTimeout ||
           err.type == DioExceptionType.receiveTimeout ||
           err.type == DioExceptionType.connectionError ||
           (err.response?.statusCode != null && err.response!.statusCode! >= 500);
  }
}
