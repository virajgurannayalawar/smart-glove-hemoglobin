import 'package:dartz/dartz.dart';
import 'package:dio/dio.dart';
import '../entities/scan_result.dart';
import '../../core/error/failures.dart';

class ScanPollResponse {
  final String status;
  final ScanResult? result;
  final String? error;

  const ScanPollResponse({
    required this.status,
    this.result,
    this.error,
  });

  bool get isPending => status == 'pending';
  bool get isCompleted => status == 'completed';
}

abstract class ScanSessionRepository {
  Future<Either<Failure, String>> createSession({
    required String patientId,
    required bool isPregnant,
  });

  Future<Either<Failure, ScanPollResponse>> pollResult({
    required String scanId,
    int timeoutSeconds = 60,
    CancelToken? cancelToken,
  });

  Future<Either<Failure, void>> cancelScan(String scanId);

  Future<Either<Failure, List<ScanResult>>> getScanHistory(String patientId);
}
