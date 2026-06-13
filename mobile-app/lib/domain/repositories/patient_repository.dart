import 'package:dartz/dartz.dart';
import '../../core/error/failures.dart';
import '../entities/patient.dart';

abstract class PatientRepository {
  /// Add a new patient
  Future<Either<Failure, Patient>> addPatient({
    required String name,
    required int age,
    required String gender,
    required String contactNumber,
    required String email,
    String? notes,
  });

  /// List all patients for current owner
  Future<Either<Failure, List<Patient>>> listPatients();

  /// Delete a patient by ID
  Future<Either<Failure, void>> deletePatient(String patientId);

  /// Get a single patient by ID
  Future<Either<Failure, Patient>> getPatient(String patientId);
}
