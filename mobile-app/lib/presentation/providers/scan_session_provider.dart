import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive_flutter/hive_flutter.dart';

import '../../core/services/bluetooth_service.dart';
import '../../data/repositories/glove_repository_impl.dart';
import '../../data/repositories/history_repository_impl.dart';
import '../../data/repositories/scan_session_repository_impl.dart';
import '../../domain/entities/scan_result.dart';
import '../../domain/repositories/glove_repository.dart';
import '../../domain/repositories/scan_session_repository.dart';
import 'history_provider.dart';

enum ScanSessionState { idle, creating, polling, success, timeout, error, cancelled }

class ScanSessionNotifierState {
  final ScanSessionState state;
  final String? scanId;
  final ScanResult? result;
  final String? errorMessage;
  final int pollAttempt;
  final int maxPollAttempts;
  final CancelToken? cancelToken;

  ScanSessionNotifierState({
    this.state = ScanSessionState.idle,
    this.scanId,
    this.result,
    this.errorMessage,
    this.pollAttempt = 0,
    this.maxPollAttempts = 3,
    this.cancelToken,
  });

  ScanSessionNotifierState copyWith({
    ScanSessionState? state,
    String? scanId,
    ScanResult? result,
    String? errorMessage,
    int? pollAttempt,
    int? maxPollAttempts,
    CancelToken? cancelToken,
  }) {
    return ScanSessionNotifierState(
      state: state ?? this.state,
      scanId: scanId ?? this.scanId,
      result: result ?? this.result,
      errorMessage: errorMessage ?? this.errorMessage,
      pollAttempt: pollAttempt ?? this.pollAttempt,
      maxPollAttempts: maxPollAttempts ?? this.maxPollAttempts,
      cancelToken: cancelToken ?? this.cancelToken,
    );
  }
}

class ScanSessionNotifier extends StateNotifier<ScanSessionNotifierState> {
  ScanSessionNotifier(
    this._repository,
    this._gloveRepository,
    this._bleService,
    this._ref,
  ) : super(ScanSessionNotifierState());

  final ScanSessionRepository _repository;
  final GloveRepository _gloveRepository;
  final BluetoothService _bleService;
  final Ref _ref;

  Future<void> startScan({
    required String patientId,
    required bool isPregnant,
    int timeoutSeconds = 60,
  }) async {
    final cancelToken = CancelToken();
    state = ScanSessionNotifierState(
      state: ScanSessionState.creating,
      cancelToken: cancelToken,
    );

    final createResult = await _repository.createSession(
      patientId: patientId,
      isPregnant: isPregnant,
    );

    final scanId = createResult.fold(
      (failure) {
        state = state.copyWith(
          state: ScanSessionState.error,
          errorMessage: failure.message,
        );
        return null;
      },
      (id) => id,
    );

    if (scanId == null || cancelToken.isCancelled) return;

    state = state.copyWith(scanId: scanId);

    final ownerResult = await _gloveRepository.fetchOwnerId();
    ownerResult.fold(
      (_) {},
      (ownerId) {
        unawaited(
          _bleService.triggerGloveLocal(
            scanId: scanId,
            ownerId: ownerId,
            patientId: patientId,
          ),
        );
      },
    );

    await _pollWithRetry(
      scanId: scanId,
      timeoutSeconds: timeoutSeconds,
      cancelToken: cancelToken,
    );
  }

  Future<void> _pollWithRetry({
    required String scanId,
    required int timeoutSeconds,
    required CancelToken cancelToken,
  }) async {
    const maxAttempts = 3;
    var delayMs = 2000;

    for (var attempt = 0; attempt < maxAttempts; attempt++) {
      if (cancelToken.isCancelled) {
        state = state.copyWith(state: ScanSessionState.cancelled);
        return;
      }

      state = state.copyWith(
        state: ScanSessionState.polling,
        pollAttempt: attempt + 1,
        maxPollAttempts: maxAttempts,
      );

      final pollResult = await _repository.pollResult(
        scanId: scanId,
        timeoutSeconds: timeoutSeconds,
        cancelToken: cancelToken,
      );

      if (cancelToken.isCancelled) {
        state = state.copyWith(state: ScanSessionState.cancelled);
        return;
      }

      final shouldContinue = await pollResult.fold(
        (failure) async {
          if (attempt < maxAttempts - 1) {
            await Future.delayed(Duration(milliseconds: delayMs));
            delayMs *= 2;
            return true;
          }
          state = state.copyWith(
            state: ScanSessionState.error,
            errorMessage: failure.message,
          );
          return false;
        },
        (response) async {
          if (response.isCompleted && response.result != null) {
            final result = response.result!;
            await _persistResult(result);
            _ref.read(historyNotifierProvider.notifier).refresh();
            state = state.copyWith(
              state: ScanSessionState.success,
              result: result,
            );
            return false;
          }

          if (response.isPending) {
            if (attempt < maxAttempts - 1) {
              await Future.delayed(Duration(milliseconds: delayMs));
              delayMs *= 2;
              return true;
            }
            state = state.copyWith(
              state: ScanSessionState.timeout,
              errorMessage: 'Scan still pending after $maxAttempts attempts',
            );
            return false;
          }

          state = state.copyWith(
            state: ScanSessionState.error,
            errorMessage: response.error ?? 'Scan ${response.status}',
          );
          return false;
        },
      );

      if (!shouldContinue) return;
    }
  }

  Future<void> _persistResult(ScanResult result) async {
    try {
      final historyBox = await Hive.openBox(HistoryRepositoryImpl.boxName);
      final cachedData = historyBox.get(HistoryRepositoryImpl.cacheKey);
      List<dynamic> items = [];
      if (cachedData is String) {
        items = jsonDecode(cachedData) as List<dynamic>;
      }
      items.insert(0, result.toJson());
      await historyBox.put(HistoryRepositoryImpl.cacheKey, jsonEncode(items));
    } catch (_) {
      // Non-fatal: remote history refresh will still run.
    }
  }

  Future<void> cancelScan() async {
    if (state.scanId == null) return;

    state.cancelToken?.cancel('User cancelled scan');

    final result = await _repository.cancelScan(state.scanId!);
    result.fold(
      (failure) => state = state.copyWith(
        state: ScanSessionState.error,
        errorMessage: 'Failed to cancel: ${failure.message}',
      ),
      (_) => state = state.copyWith(state: ScanSessionState.cancelled),
    );
  }

  Future<void> retryScan({int timeoutSeconds = 60}) async {
    if (state.scanId == null) return;

    final cancelToken = CancelToken();
    state = state.copyWith(
      state: ScanSessionState.polling,
      errorMessage: null,
      cancelToken: cancelToken,
    );

    await _pollWithRetry(
      scanId: state.scanId!,
      timeoutSeconds: timeoutSeconds,
      cancelToken: cancelToken,
    );
  }

  void resetSession() {
    state.cancelToken?.cancel('Reset');
    state = ScanSessionNotifierState();
  }
}

final scanSessionNotifierProvider =
    StateNotifierProvider<ScanSessionNotifier, ScanSessionNotifierState>(
  (ref) {
    final notifier = ScanSessionNotifier(
      ref.watch(scanSessionRepositoryProvider),
      ref.watch(gloveRepositoryProvider),
      ref.watch(bluetoothServiceProvider.notifier),
      ref,
    );
    ref.onDispose(() => notifier.resetSession());
    return notifier;
  },
);
