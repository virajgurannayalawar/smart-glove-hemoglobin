import 'dart:async';
import 'dart:convert';
import 'package:flutter_blue_plus/flutter_blue_plus.dart' as fbp;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:http/http.dart' as http;
import '../constants/bluetooth_constants.dart';

enum BleConnectionState { disconnected, scanning, connected, provisioning, provisioned, error }

class BleState {
  final BleConnectionState connectionState;
  final String statusMessage;
  final List<fbp.ScanResult> availableDevices;
  final fbp.BluetoothDevice? selectedDevice;
  final bool isProvisioned;

  BleState({
    this.connectionState = BleConnectionState.disconnected,
    this.statusMessage = 'Disconnected',
    this.availableDevices = const [],
    this.selectedDevice,
    this.isProvisioned = false,
  });

  BleState copyWith({
    BleConnectionState? connectionState,
    String? statusMessage,
    List<fbp.ScanResult>? availableDevices,
    fbp.BluetoothDevice? selectedDevice,
    bool? isProvisioned,
  }) {
    return BleState(
      connectionState: connectionState ?? this.connectionState,
      statusMessage: statusMessage ?? this.statusMessage,
      availableDevices: availableDevices ?? this.availableDevices,
      selectedDevice: selectedDevice ?? this.selectedDevice,
      isProvisioned: isProvisioned ?? this.isProvisioned,
    );
  }
}

final bluetoothServiceProvider =
    StateNotifierProvider<BluetoothService, BleState>((ref) {
  return BluetoothService();
});

class BluetoothService extends StateNotifier<BleState> {
  fbp.BluetoothDevice? _connectedDevice;
  fbp.BluetoothCharacteristic? _statusCharacteristic;
  fbp.BluetoothCharacteristic? _writeCharacteristic;
  StreamSubscription<List<fbp.ScanResult>>? _scanSubscription;
  StreamSubscription<fbp.BluetoothConnectionState>? _connectionSubscription;
  StreamSubscription<List<int>>? _characteristicSubscription;
  bool _autoReconnect = true;

  BluetoothService() : super(BleState()) {
    _initBluetooth();
  }

  Future<void> _initBluetooth() async {
    if (await fbp.FlutterBluePlus.isSupported == false) {
      state = state.copyWith(
          connectionState: BleConnectionState.error,
          statusMessage: 'Bluetooth not supported');
      return;
    }

    fbp.FlutterBluePlus.adapterState.listen((adapterState) {
      if (adapterState == fbp.BluetoothAdapterState.on) {
        // Auto-start scan if not connected
        if (state.connectionState != BleConnectionState.connected &&
            state.connectionState != BleConnectionState.provisioning) {
          startScan();
        }
      } else {
        state = state.copyWith(
            connectionState: BleConnectionState.disconnected,
            statusMessage: 'Bluetooth is off');
      }
    });
  }

  /// Start scanning for devices with the Smart Glove service
  Future<void> startScan() async {
    if (state.connectionState == BleConnectionState.connected ||
        state.connectionState == BleConnectionState.provisioning) return;

    state = state.copyWith(
        connectionState: BleConnectionState.scanning,
        statusMessage: 'Scanning for Smart Glove...',
        availableDevices: []);

    await fbp.FlutterBluePlus.startScan(
      withServices: [fbp.Guid(BluetoothConstants.serviceUuid)],
      timeout: const Duration(seconds: 15),
    );

    _scanSubscription = fbp.FlutterBluePlus.scanResults.listen((results) {
      state = state.copyWith(availableDevices: results);
    });
  }

  /// Stop scanning
  Future<void> stopScan() async {
    await fbp.FlutterBluePlus.stopScan();
    _scanSubscription?.cancel();
    state = state.copyWith(
      connectionState: BleConnectionState.disconnected,
      availableDevices: [],
      statusMessage: 'Scan stopped',
    );
  }

  /// Manually select and connect to a device
  Future<bool> selectAndConnect(fbp.BluetoothDevice device) async {
    try {
      await fbp.FlutterBluePlus.stopScan();
      _scanSubscription?.cancel();

      _connectedDevice = device;
      _autoReconnect = true;

      state = state.copyWith(
          selectedDevice: device,
          connectionState: BleConnectionState.scanning,
          statusMessage: 'Connecting to ${device.advName}...');

      _connectionSubscription = device.connectionState.listen((connectionState) async {
        if (connectionState == fbp.BluetoothConnectionState.connected) {
          state = state.copyWith(
              connectionState: BleConnectionState.connected,
              statusMessage: 'Connected. Discovering services...');
          await _discoverServices(device);
        } else if (connectionState == fbp.BluetoothConnectionState.disconnected) {
          state = state.copyWith(
              connectionState: BleConnectionState.disconnected,
              statusMessage: 'Disconnected');
          _cleanup();
          if (_autoReconnect) {
            Future.delayed(const Duration(seconds: 5), startScan);
          }
        }
      });

      await device.connect(autoConnect: false);
      return true;
    } catch (e) {
      state = state.copyWith(
          connectionState: BleConnectionState.error,
          statusMessage: 'Failed to connect: ${e.toString()}');
      return false;
    }
  }

  /// Discover services and characteristics
  Future<void> _discoverServices(fbp.BluetoothDevice device) async {
    try {
      List<fbp.BluetoothService> services = await device.discoverServices();
      for (var service in services) {
        if (service.uuid.toString().toLowerCase() ==
            BluetoothConstants.serviceUuid) {
          for (var characteristic in service.characteristics) {
            final uuid = characteristic.uuid.toString().toLowerCase();
            if (uuid == BluetoothConstants.characteristicUuid) {
              _statusCharacteristic = characteristic;
              _writeCharacteristic = characteristic;

              // Enable notifications if supported
              if (characteristic.properties.notify) {
                await characteristic.setNotifyValue(true);
                _characteristicSubscription =
                    characteristic.lastValueStream.listen((value) {
                  if (value.isNotEmpty) {
                    final statusStr = String.fromCharCodes(value);
                    state = state.copyWith(statusMessage: statusStr);
                  }
                });
              }

              state = state.copyWith(
                  connectionState: BleConnectionState.connected,
                  statusMessage: 'Connected: Ready to provision');
              return;
            }
          }
        }
      }
      state = state.copyWith(
          connectionState: BleConnectionState.error,
          statusMessage: 'Required GATT service not found');
    } catch (e) {
      state = state.copyWith(
          connectionState: BleConnectionState.error,
          statusMessage: 'Service discovery failed: ${e.toString()}');
    }
  }

  /// Send provisioning payload to glove over BLE
  /// payload: { owner_id, glove_api_key, wifi_ssid, wifi_password }
  Future<bool> sendProvisioningPayload(Map<String, String> payload) async {
    if (_writeCharacteristic == null) {
      state = state.copyWith(
          connectionState: BleConnectionState.error,
          statusMessage: 'Characteristic not found. Reconnect device.');
      return false;
    }

    try {
      state = state.copyWith(
          connectionState: BleConnectionState.provisioning,
          statusMessage: 'Provisioning glove...');

      final jsonPayload = jsonEncode(payload);
      final bytes = utf8.encode(jsonPayload);

      // Write with response if supported
      if (_writeCharacteristic!.properties.write) {
        await _writeCharacteristic!.write(bytes, withoutResponse: false);
        state = state.copyWith(
            connectionState: BleConnectionState.provisioned,
            statusMessage: 'Provisioning successful!',
            isProvisioned: true);
        return true;
      } else if (_writeCharacteristic!.properties.writeWithoutResponse) {
        await _writeCharacteristic!.write(bytes, withoutResponse: true);
        state = state.copyWith(
            connectionState: BleConnectionState.provisioned,
            statusMessage: 'Provisioning data sent (no response).',
            isProvisioned: true);
        return true;
      } else {
        state = state.copyWith(
            connectionState: BleConnectionState.error,
            statusMessage: 'Characteristic does not support write.');
        return false;
      }
    } catch (e) {
      state = state.copyWith(
          connectionState: BleConnectionState.error,
          statusMessage: 'Provisioning failed: ${e.toString()}');
      return false;
    }
  }

  /// Trigger a local scan on the glove via HTTP (mDNS)
  /// This prepares the glove to capture an image for a given scan session
  /// Uses mDNS for discovery: http://glove-{owner_id}.local:5000/trigger
  Future<bool> triggerGloveLocal({
    required String scanId,
    required String ownerId,
    required String patientId,
  }) async {
    try {
      state = state.copyWith(statusMessage: 'Triggering glove scan...');

      // Use mDNS hostname for glove discovery
      final hostname = 'glove-$ownerId.local';
      const port = 5000;
      const timeout = Duration(seconds: 5);

      final uri = Uri(
        scheme: 'http',
        host: hostname,
        port: port,
        path: '/trigger',
      );

      final response = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'scan_id': scanId,
              'owner_id': ownerId,
              'patient_id': patientId,
              'timestamp': DateTime.now().toIso8601String(),
            }),
          )
          .timeout(timeout, onTimeout: () {
        throw TimeoutException('Glove not reachable - timeout after 5s');
      });

      if (response.statusCode == 200 || response.statusCode == 202) {
        state = state.copyWith(
            statusMessage: 'Glove triggered successfully');
        return true;
      } else if (response.statusCode == 408) {
        // Glove returned timeout - scanning already in progress
        state = state.copyWith(
            statusMessage: 'Glove busy - scan already in progress');
        return false;
      } else {
        state = state.copyWith(
            statusMessage:
                'Glove trigger failed: HTTP ${response.statusCode}');
        return false;
      }
    } on TimeoutException catch (e) {
      // Common case: glove is offline
      state = state.copyWith(
          statusMessage: 'Glove unreachable - proceeding with backend poll');
      // Return true anyway - backend polling will complete the scan
      return true;
    } catch (e) {
      state = state.copyWith(
          statusMessage:
              'Local trigger error: ${e.toString()}, using backend only');
      // Return true - don't fail, use backend polling instead
      return true;
    }
  }

  /// Disconnect from the glove and reset state
  Future<void> disconnect() async {
    _autoReconnect = false;
    await _connectedDevice?.disconnect();
    _cleanup();
    state = BleState();
  }

  void _cleanup() {
    _characteristicSubscription?.cancel();
    _statusCharacteristic = null;
    _writeCharacteristic = null;
    _connectedDevice = null;
  }

  @override
  void dispose() {
    fbp.FlutterBluePlus.stopScan();
    _scanSubscription?.cancel();
    _connectionSubscription?.cancel();
    _characteristicSubscription?.cancel();
    _connectedDevice?.disconnect();
    super.dispose();
  }
}
