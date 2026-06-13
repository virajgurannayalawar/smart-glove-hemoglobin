import 'package:dartz/dartz.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:smart_glove/core/error/failures.dart';
import 'package:smart_glove/domain/entities/scan_result.dart';
import 'package:smart_glove/domain/repositories/scan_session_repository.dart';

class FakeScanRepository implements ScanSessionRepository {
  int pollCalls = 0;

  @override
  Future<Either<Failure, String>> createSession({
    required String patientId,
    required bool isPregnant,
  }) async {
    return const Right('scan-test-1');
  }

  @override
  Future<Either<Failure, ScanPollResponse>> pollResult({
    required String scanId,
    int timeoutSeconds = 60,
    CancelToken? cancelToken,
  }) async {
    pollCalls++;
    if (pollCalls == 1) {
      return const Right(ScanPollResponse(status: 'pending'));
    }
    return Right(
      ScanPollResponse(
        status: 'completed',
        result: ScanResult(
          id: 'reading-1',
          scanId: scanId,
          date: DateTime.parse('2026-06-05T10:00:00.000Z'),
          hemoglobinLevel: 12.5,
          isAnemic: false,
          statusText: 'Normal',
        ),
      ),
    );
  }

  @override
  Future<Either<Failure, void>> uploadScanImage({
    required String scanId,
    required List<int> encryptedImageBytes,
    required String ownerId,
    required String patientId,
    required bool isPregnant,
    required String gloveKey,
  }) async {
    return const Right(null);
  }

  @override
  Future<Either<Failure, void>> cancelScan(String scanId) async {
    return const Right(null);
  }

  @override
  Future<Either<Failure, List<ScanResult>>> getScanHistory(String patientId) async {
    return Right(<ScanResult>[]);
  }
}

void main() {
  test('mock repository returns pending then completed on consecutive polls', () async {
    final repo = FakeScanRepository();

    final first = await repo.pollResult(scanId: 'scan-1');
    first.fold(
      (_) => fail('expected pending response'),
      (response) => expect(response.isPending, isTrue),
    );

    final second = await repo.pollResult(scanId: 'scan-1');
    second.fold(
      (_) => fail('expected completed response'),
      (response) {
        expect(response.isCompleted, isTrue);
        expect(response.result?.hemoglobinLevel, 12.5);
      },
    );

    expect(repo.pollCalls, 2);
  });
}
