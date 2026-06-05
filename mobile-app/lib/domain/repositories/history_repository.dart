import 'package:dartz/dartz.dart';
import '../../core/error/failures.dart';
import '../entities/scan_result.dart';

abstract class HistoryRepository {
  Future<Either<Failure, List<ScanResult>>> getHistory();
}
