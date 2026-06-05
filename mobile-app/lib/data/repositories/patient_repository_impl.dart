import 'package:dartz/dartz.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive/hive.dart';

import '../../core/error/failures.dart';
import '../../core/network/dio_provider.dart';
import '../../domain/entities/patient.dart';
import '../../domain/repositories/patient_repository.dart';

final patientRepositoryProvider = Provider<PatientRepository>((ref) {
  return PatientRepositoryImpl(
    dio: ref.watch(dioProvider),
  );
});

class PatientRepositoryImpl implements PatientRepository {
  final Dio dio;
  static const String _patientsBoxKey = 'patientsBox';
  static const String _patientsListKey = 'patients_list';

  PatientRepositoryImpl({required this.dio});

  @override
  Future<Either<Failure, Patient>> addPatient({
    required String name,
    required int age,
    required String gender,
    required String contactNumber,
    required String email,
    String? notes,
  }) async {
    try {
      final response = await dio.post(
        '/patients',
        data: {
          'Name': name,
          'Age': age,
          'Gender': gender,
          'ContactNumber': contactNumber,
          'Email': email,
          'Notes': notes,
        },
      );

      if (response.statusCode == 201 || response.statusCode == 200) {
        final patient = Patient.fromJson(response.data as Map<String, dynamic>);
        await _cachePatient(patient);
        return Right(patient);
      }

      return Left(ServerFailure(
        (response.data as Map?)?['detail']?.toString() ?? 'Failed to add patient',
      ));
    } on DioException catch (e) {
      return _mapDioError(e, 'Failed to add patient');
    } catch (e) {
      return const Left(ServerFailure('An unexpected error occurred'));
    }
  }

  @override
  Future<Either<Failure, List<Patient>>> listPatients() async {
    try {
      final response = await dio.get('/patients');

      if (response.statusCode == 200) {
        List<dynamic> patientList = [];
        if (response.data is List) {
          patientList = response.data as List;
        } else if (response.data is Map && response.data['patients'] is List) {
          patientList = response.data['patients'] as List;
        }

        final patients = patientList
            .map((json) => Patient.fromJson(json as Map<String, dynamic>))
            .toList();

        await _cachePatients(patients);
        return Right(patients);
      }

      return const Left(ServerFailure('Failed to fetch patients'));
    } on DioException catch (e) {
      try {
        final box = await Hive.openBox(_patientsBoxKey);
        final cachedJson = box.get(_patientsListKey) as List?;
        if (cachedJson != null && cachedJson.isNotEmpty) {
          return Right(
            cachedJson
                .cast<Map<String, dynamic>>()
                .map(Patient.fromJson)
                .toList(),
          );
        }
      } catch (_) {}

      return _mapDioError(e, 'Failed to fetch patients');
    } catch (e) {
      return const Left(ServerFailure('An unexpected error occurred'));
    }
  }

  @override
  Future<Either<Failure, void>> deletePatient(String patientId) async {
    try {
      final response = await dio.delete('/patients/$patientId');

      if (response.statusCode == 204 || response.statusCode == 200) {
        await _removePatientFromCache(patientId);
        return const Right(null);
      }

      return const Left(ServerFailure('Failed to delete patient'));
    } on DioException catch (e) {
      return _mapDioError(e, 'Failed to delete patient');
    } catch (e) {
      return const Left(ServerFailure('An unexpected error occurred'));
    }
  }

  @override
  Future<Either<Failure, Patient>> getPatient(String patientId) async {
    try {
      try {
        final box = await Hive.openBox(_patientsBoxKey);
        final cachedJson = box.get('patient_$patientId');
        if (cachedJson != null) {
          return Right(Patient.fromJson(cachedJson as Map<String, dynamic>));
        }
      } catch (_) {}

      final response = await dio.get('/patients/$patientId');

      if (response.statusCode == 200) {
        final patient = Patient.fromJson(response.data as Map<String, dynamic>);
        await _cachePatient(patient);
        return Right(patient);
      }

      return const Left(ServerFailure('Patient not found'));
    } on DioException catch (e) {
      return _mapDioError(e, 'Failed to fetch patient');
    } catch (e) {
      return const Left(ServerFailure('An unexpected error occurred'));
    }
  }

  Future<void> _cachePatient(Patient patient) async {
    try {
      final box = await Hive.openBox(_patientsBoxKey);
      await box.put('patient_${patient.id}', patient.toJson());
    } catch (_) {}
  }

  Future<void> _cachePatients(List<Patient> patients) async {
    try {
      final box = await Hive.openBox(_patientsBoxKey);
      await box.put(
        _patientsListKey,
        patients.map((p) => p.toJson()).toList(),
      );
    } catch (_) {}
  }

  Future<void> _removePatientFromCache(String patientId) async {
    try {
      final box = await Hive.openBox(_patientsBoxKey);
      await box.delete('patient_$patientId');

      final listJson = box.get(_patientsListKey) as List?;
      if (listJson != null) {
        final updated = listJson
            .where((json) => (json as Map)['id'] != patientId &&
                (json as Map)['PatientId'] != patientId)
            .toList();
        await box.put(_patientsListKey, updated);
      }
    } catch (_) {}
  }

  Either<Failure, T> _mapDioError<T>(DioException e, String fallback) {
    if (e.type == DioExceptionType.receiveTimeout) {
      return Left(NetworkFailure('$fallback: timeout'));
    }
    if (e.response != null) {
      final detail = e.response?.data;
      final message = detail is Map
          ? (detail['detail'] ?? detail['message'] ?? fallback).toString()
          : fallback;
      return Left(ServerFailure(message));
    }
    return Left(NetworkFailure('$fallback: network error'));
  }
}
