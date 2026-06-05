import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/error/failures.dart';
import '../../data/repositories/patient_repository_impl.dart';
import '../../domain/entities/patient.dart';
import '../../domain/repositories/patient_repository.dart';

class PatientState {
  final bool isLoading;
  final List<Patient> patients;
  final Patient? selectedPatient;
  final String? errorMessage;

  PatientState({
    this.isLoading = false,
    this.patients = const [],
    this.selectedPatient,
    this.errorMessage,
  });

  PatientState copyWith({
    bool? isLoading,
    List<Patient>? patients,
    Patient? selectedPatient,
    String? errorMessage,
    bool clearError = false,
    bool clearSelected = false,
  }) {
    return PatientState(
      isLoading: isLoading ?? this.isLoading,
      patients: patients ?? this.patients,
      selectedPatient: clearSelected ? null : (selectedPatient ?? this.selectedPatient),
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }
}

final patientNotifierProvider = StateNotifierProvider<PatientNotifier, PatientState>((ref) {
  return PatientNotifier(ref.watch(patientRepositoryProvider));
});

class PatientNotifier extends StateNotifier<PatientState> {
  final PatientRepository _patientRepository;

  PatientNotifier(this._patientRepository) : super(PatientState()) {
    loadPatients();
  }

  /// Load all patients
  Future<void> loadPatients() async {
    state = state.copyWith(isLoading: true, clearError: true);

    final result = await _patientRepository.listPatients();

    result.fold(
      (failure) {
        state = state.copyWith(
          isLoading: false,
          errorMessage: failure.message,
        );
      },
      (patients) {
        state = state.copyWith(
          isLoading: false,
          patients: patients,
        );
      },
    );
  }

  /// Add a new patient
  Future<bool> addPatient({
    required String name,
    required int age,
    required String gender,
    required String contactNumber,
    required String email,
    String? notes,
  }) async {
    state = state.copyWith(isLoading: true, clearError: true);

    final result = await _patientRepository.addPatient(
      name: name,
      age: age,
      gender: gender,
      contactNumber: contactNumber,
      email: email,
      notes: notes,
    );

    return result.fold(
      (failure) {
        state = state.copyWith(
          isLoading: false,
          errorMessage: failure.message,
        );
        return false;
      },
      (newPatient) {
        final updatedPatients = [...state.patients, newPatient];
        state = state.copyWith(
          isLoading: false,
          patients: updatedPatients,
        );
        return true;
      },
    );
  }

  /// Delete a patient
  Future<bool> deletePatient(String patientId) async {
    final result = await _patientRepository.deletePatient(patientId);

    return result.fold(
      (failure) {
        state = state.copyWith(
          errorMessage: failure.message,
        );
        return false;
      },
      (_) {
        final updatedPatients = state.patients.where((p) => p.id != patientId).toList();
        state = state.copyWith(
          patients: updatedPatients,
          clearSelected: state.selectedPatient?.id == patientId,
        );
        return true;
      },
    );
  }

  /// Select a patient for scanning
  void selectPatient(Patient patient) {
    state = state.copyWith(selectedPatient: patient);
  }

  /// Clear selection
  void clearSelection() {
    state = state.copyWith(clearSelected: true);
  }

  /// Refresh patients list
  Future<void> refresh() async {
    await loadPatients();
  }
}
