import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../domain/entities/scan_result.dart';
import '../../data/repositories/history_repository_impl.dart';
import '../../domain/repositories/history_repository.dart';

final historyNotifierProvider = StateNotifierProvider<HistoryNotifier, HistoryState>((ref) {
  return HistoryNotifier(ref.watch(historyRepositoryProvider));
});

class HistoryState {
  final bool isLoading;
  final List<ScanResult> scans;
  final String? errorMessage;

  HistoryState({
    this.isLoading = false,
    this.scans = const [],
    this.errorMessage,
  });

  HistoryState copyWith({
    bool? isLoading,
    List<ScanResult>? scans,
    String? errorMessage,
    bool clearError = false,
  }) {
    return HistoryState(
      isLoading: isLoading ?? this.isLoading,
      scans: scans ?? this.scans,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }
}

class HistoryNotifier extends StateNotifier<HistoryState> {
  final HistoryRepository _historyRepository;

  HistoryNotifier(this._historyRepository) : super(HistoryState()) {
    fetchHistory();
  }

  Future<void> refresh() => fetchHistory();

  Future<void> fetchHistory() async {
    state = state.copyWith(isLoading: true, clearError: true);
    
    final result = await _historyRepository.getHistory();
    
    result.fold(
      (failure) {
        state = state.copyWith(isLoading: false, errorMessage: failure.message);
      },
      (scans) {
        final sorted = [...scans]..sort((a, b) => b.date.compareTo(a.date));
        state = state.copyWith(isLoading: false, scans: sorted);
      },
    );
  }
}
