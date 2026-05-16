import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/entities/user.dart';
import '../../data/repositories/profile_repository_impl.dart';
import '../../domain/repositories/profile_repository.dart';
import 'auth_provider.dart';

final profileNotifierProvider = StateNotifierProvider<ProfileNotifier, ProfileState>((ref) {
  return ProfileNotifier(
    ref.watch(profileRepositoryProvider),
    ref,
  );
});

class ProfileState {
  final bool isLoading;
  final User? profile;
  final String? errorMessage;
  final bool isSuccess;

  ProfileState({
    this.isLoading = false,
    this.profile,
    this.errorMessage,
    this.isSuccess = false,
  });

  ProfileState copyWith({
    bool? isLoading,
    User? profile,
    String? errorMessage,
    bool? isSuccess,
    bool clearError = false,
  }) {
    return ProfileState(
      isLoading: isLoading ?? this.isLoading,
      profile: profile ?? this.profile,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      isSuccess: isSuccess ?? this.isSuccess,
    );
  }
}

class ProfileNotifier extends StateNotifier<ProfileState> {
  final ProfileRepository _profileRepository;
  final Ref _ref;

  ProfileNotifier(this._profileRepository, this._ref) : super(ProfileState()) {
    fetchProfile();
  }

  Future<void> fetchProfile() async {
    state = state.copyWith(isLoading: true, clearError: true, isSuccess: false);
    
    final result = await _profileRepository.getProfile();
    
    result.fold(
      (failure) {
        state = state.copyWith(isLoading: false, errorMessage: failure.message);
      },
      (profile) {
        state = state.copyWith(isLoading: false, profile: profile);
      },
    );
  }

  Future<bool> updateProfile({
    required String name,
    required int age,
    required String gender,
  }) async {
    state = state.copyWith(isLoading: true, clearError: true, isSuccess: false);
    
    final result = await _profileRepository.updateProfile(
      name: name,
      age: age,
      gender: gender,
    );
    
    return result.fold(
      (failure) {
        state = state.copyWith(isLoading: false, errorMessage: failure.message);
        return false;
      },
      (profile) {
        state = state.copyWith(isLoading: false, profile: profile, isSuccess: true);
        // Also update AuthNotifier to reflect changes globally
        _ref.read(authNotifierProvider.notifier).fetchProfileSilently(profile); // We'll add this method
        return true;
      },
    );
  }
}
