import 'package:flutter_blue_plus/flutter_blue_plus.dart' as fbp;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hive/hive.dart';
import '../../core/services/bluetooth_service.dart';
import '../../data/repositories/glove_repository_impl.dart';
import '../../domain/repositories/glove_repository.dart';

/// Provisioning progress states
enum ProvisioningState {
  idle,
  fetchingCredentials,
  scanning,
  connecting,
  provisioning,
  success,
  error,
}

class ConnectGloveState {
  final ProvisioningState state;
  final String statusMessage;
  final String? errorMessage;
  final List<fbp.ScanResult> availableDevices;
  final fbp.BluetoothDevice? selectedDevice;
  final bool isProvisioned;

  ConnectGloveState({
    this.state = ProvisioningState.idle,
    this.statusMessage = 'Ready to connect',
    this.errorMessage,
    this.availableDevices = const [],
    this.selectedDevice,
    this.isProvisioned = false,
  });

  ConnectGloveState copyWith({
    ProvisioningState? state,
    String? statusMessage,
    String? errorMessage,
    List<fbp.ScanResult>? availableDevices,
    fbp.BluetoothDevice? selectedDevice,
    bool? isProvisioned,
    bool clearError = false,
  }) {
    return ConnectGloveState(
      state: state ?? this.state,
      statusMessage: statusMessage ?? this.statusMessage,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      availableDevices: availableDevices ?? this.availableDevices,
      selectedDevice: selectedDevice ?? this.selectedDevice,
      isProvisioned: isProvisioned ?? this.isProvisioned,
    );
  }
}

final connectGloveNotifierProvider =
    StateNotifierProvider<ConnectGloveNotifier, ConnectGloveState>((ref) {
  return ConnectGloveNotifier(
    bleService: ref.watch(bluetoothServiceProvider.notifier),
    gloveRepository: ref.watch(gloveRepositoryProvider),
  );
});

class ConnectGloveNotifier extends StateNotifier<ConnectGloveState> {
  final BluetoothService _bleService;
  final GloveRepository _gloveRepository;

  static const String _provisioningBoxKey = 'glovebox';
  static const String _provisionedFlagKey = 'is_provisioned';

  ConnectGloveNotifier({
    required BluetoothService bleService,
    required GloveRepository gloveRepository,
  })  : _bleService = bleService,
        _gloveRepository = gloveRepository,
        super(ConnectGloveState()) {
    _initProvisioningState();
  }

  /// Load provisioning state from Hive
  Future<void> _initProvisioningState() async {
    try {
      final box = await Hive.openBox(_provisioningBoxKey);
      final isProvisioned = box.get(_provisionedFlagKey, defaultValue: false) as bool;
      state = state.copyWith(isProvisioned: isProvisioned);
    } catch (e) {
      // Box might not exist yet, that's ok
    }
  }

  /// Start BLE scan for available devices
  Future<void> startScan() async {
    state = state.copyWith(
      state: ProvisioningState.scanning,
      statusMessage: 'Scanning for Smart Glove...',
      clearError: true,
    );

    await _bleService.startScan();
  }

  /// Stop BLE scan
  Future<void> stopScan() async {
    await _bleService.stopScan();
    state = state.copyWith(
      state: ProvisioningState.idle,
      statusMessage: 'Scan stopped',
      availableDevices: [],
    );
  }

  /// Select a device from the scan results and connect
  Future<bool> selectDevice(fbp.BluetoothDevice device) async {
    state = state.copyWith(
      state: ProvisioningState.connecting,
      selectedDevice: device,
      statusMessage: 'Connecting to ${device.advName}...',
      clearError: true,
    );

    final success = await _bleService.selectAndConnect(device);
    if (!success) {
      state = state.copyWith(
        state: ProvisioningState.error,
        errorMessage: 'Failed to connect to device',
        statusMessage: 'Connection failed. Try again.',
      );
      return false;
    }

    state = state.copyWith(
      state: ProvisioningState.idle,
      statusMessage: 'Connected. Ready to provision.',
    );
    return true;
  }

  /// Fetch provisioning credentials from backend
  Future<Map<String, String>?> fetchProvisioningCredentials(
      {required String wifiSsid, required String wifiPassword}) async {
    state = state.copyWith(
      state: ProvisioningState.fetchingCredentials,
      statusMessage: 'Fetching provisioning credentials...',
      clearError: true,
    );

    try {
      final ownerId = await _gloveRepository.fetchOwnerId();
      final gloveKey = await _gloveRepository.fetchGloveKey();

      ownerId.fold(
        (failure) {
          state = state.copyWith(
            state: ProvisioningState.error,
            errorMessage: 'Failed to fetch owner ID: ${failure.message}',
          );
          throw Exception(failure.message);
        },
        (id) {
          // Success
        },
      );

      gloveKey.fold(
        (failure) {
          state = state.copyWith(
            state: ProvisioningState.error,
            errorMessage: 'Failed to fetch glove key: ${failure.message}',
          );
          throw Exception(failure.message);
        },
        (key) {
          // Success
        },
      );

      // Extract values from Either
      final ownerIdValue = ownerId.getOrElse(() => '');
      final gloveKeyValue = gloveKey.getOrElse(() => '');

      if (ownerIdValue.isEmpty || gloveKeyValue.isEmpty) {
        state = state.copyWith(
          state: ProvisioningState.error,
          errorMessage: 'Credentials are empty',
        );
        return null;
      }

      return {
        'owner_id': ownerIdValue,
        'glove_api_key': gloveKeyValue,
        'wifi_ssid': wifiSsid,
        'wifi_password': wifiPassword,
      };
    } catch (e) {
      state = state.copyWith(
        state: ProvisioningState.error,
        errorMessage: 'Error fetching credentials: ${e.toString()}',
      );
      return null;
    }
  }

  /// Send provisioning payload to glove
  Future<bool> sendProvisioning(Map<String, String> payload) async {
    state = state.copyWith(
      state: ProvisioningState.provisioning,
      statusMessage: 'Sending provisioning data...',
      clearError: true,
    );

    final success = await _bleService.sendProvisioningPayload(payload);

    if (!success) {
      state = state.copyWith(
        state: ProvisioningState.error,
        errorMessage: 'Failed to send provisioning data',
        statusMessage: 'Provisioning failed. Try again.',
      );
      return false;
    }

    // Mark as provisioned and save to Hive
    await _saveProvisioningState(true);

    state = state.copyWith(
      state: ProvisioningState.success,
      statusMessage: 'Glove provisioned successfully!',
      isProvisioned: true,
    );

    return true;
  }

  /// Complete provisioning workflow in one call
  /// Returns true if successful
  Future<bool> completeProvisioning({
    required fbp.BluetoothDevice device,
    required String wifiSsid,
    required String wifiPassword,
  }) async {
    try {
      // Step 1: Connect to device
      final connected = await selectDevice(device);
      if (!connected) return false;

      // Step 2: Fetch credentials
      final credentials = await fetchProvisioningCredentials(
        wifiSsid: wifiSsid,
        wifiPassword: wifiPassword,
      );
      if (credentials == null) return false;

      // Step 3: Send provisioning
      final provisioned = await sendProvisioning(credentials);
      return provisioned;
    } catch (e) {
      state = state.copyWith(
        state: ProvisioningState.error,
        errorMessage: 'Provisioning workflow failed: ${e.toString()}',
      );
      return false;
    }
  }

  /// Disconnect from glove
  Future<void> disconnect() async {
    await _bleService.disconnect();
    state = state.copyWith(
      state: ProvisioningState.idle,
      selectedDevice: null,
      statusMessage: 'Disconnected',
    );
  }

  /// Re-provision (rotate glove key and re-provision)
  Future<bool> reprovisioning({
    required String wifiSsid,
    required String wifiPassword,
  }) async {
    state = state.copyWith(
      state: ProvisioningState.fetchingCredentials,
      statusMessage: 'Rotating glove key...',
      clearError: true,
    );

    try {
      // Call backend to rotate key
      final result = await _gloveRepository.rotateGloveKey();

      result.fold(
        (failure) {
          state = state.copyWith(
            state: ProvisioningState.error,
            errorMessage: 'Failed to rotate key: ${failure.message}',
          );
        },
        (newKey) {
          // Key rotated successfully
          state = state.copyWith(
            statusMessage: 'New key generated. Re-provisioning...',
          );
        },
      );

      // Proceed with provisioning
      final credentials = await fetchProvisioningCredentials(
        wifiSsid: wifiSsid,
        wifiPassword: wifiPassword,
      );
      if (credentials == null) return false;

      final provisioned = await sendProvisioning(credentials);
      return provisioned;
    } catch (e) {
      state = state.copyWith(
        state: ProvisioningState.error,
        errorMessage: 'Re-provisioning failed: ${e.toString()}',
      );
      return false;
    }
  }

  /// Reset to idle state
  void reset() {
    state = ConnectGloveState(isProvisioned: state.isProvisioned);
  }

  /// Save provisioning state to Hive
  Future<void> _saveProvisioningState(bool isProvisioned) async {
    try {
      final box = await Hive.openBox(_provisioningBoxKey);
      await box.put(_provisionedFlagKey, isProvisioned);
    } catch (e) {
      // Silently fail if box operations fail
      print('Failed to save provisioning state: $e');
    }
  }
}
