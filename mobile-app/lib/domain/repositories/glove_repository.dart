import 'package:dartz/dartz.dart';
import '../../core/error/failures.dart';

abstract class GloveRepository {
  /// Fetch the owner ID for this user (used in provisioning)
  Future<Either<Failure, String>> fetchOwnerId();

  /// Fetch the current glove API key (used in provisioning)
  Future<Either<Failure, String>> fetchGloveKey();

  /// Rotate the glove API key (for re-provisioning)
  Future<Either<Failure, String>> rotateGloveKey();
}
