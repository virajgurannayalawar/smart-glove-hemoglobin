import 'dart:async';
import 'package:flutter_blue_plus/flutter_blue_plus.dart' as fbp;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../constants/bluetooth_constants.dart';

enum BleConnectionState { disconnected, scanning, connected, error }

class BleState {
  final BleConnectionState connectionState;
  final String statusMessage;

  BleState({
    this.connectionState = BleConnectionState.disconnected,
    this.statusMessage = 'Disconnected',
  });

  BleState copyWith({
    BleConnectionState? connectionState,
    String? statusMessage,
  }) {
    return BleState(
      connectionState: connectionState ?? this.connectionState,
      statusMessage: statusMessage ?? this.statusMessage,
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
  StreamSubscription<List<fbp.ScanResult>>? _scanSubscription;
  StreamSubscription<fbp.BluetoothConnectionState>? _connectionSubscription;
  StreamSubscription<List<int>>? _characteristicSubscription;

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
        startScan();
      } else {
        state = state.copyWith(
            connectionState: BleConnectionState.disconnected,
            statusMessage: 'Bluetooth is off');
      }
    });
  }

  void startScan() async {
    if (state.connectionState == BleConnectionState.connected) return;

    state = state.copyWith(
        connectionState: BleConnectionState.scanning,
        statusMessage: 'Scanning for Smart Glove...');

    await fbp.FlutterBluePlus.startScan(
      withServices: [fbp.Guid(BluetoothConstants.serviceUuid)],
      timeout: const Duration(seconds: 15),
    );

    _scanSubscription = fbp.FlutterBluePlus.scanResults.listen((results) {
      for (fbp.ScanResult r in results) {
        if (r.advertisementData.serviceUuids
            .contains(fbp.Guid(BluetoothConstants.serviceUuid))) {
          _connectToDevice(r.device);
          break;
        }
      }
    });
  }

  Future<void> _connectToDevice(fbp.BluetoothDevice device) async {
    await fbp.FlutterBluePlus.stopScan();
    _scanSubscription?.cancel();

    _connectedDevice = device;
    state = state.copyWith(statusMessage: 'Connecting...');

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
        Future.delayed(const Duration(seconds: 5), startScan);
      }
    });

    try {
      await device.connect(autoConnect: false);
    } catch (e) {
      state = state.copyWith(
          connectionState: BleConnectionState.error,
          statusMessage: 'Failed to connect');
    }
  }

  Future<void> _discoverServices(fbp.BluetoothDevice device) async {
    List<fbp.BluetoothService> services = await device.discoverServices();
    for (var service in services) {
      if (service.uuid.toString().toLowerCase() ==
          BluetoothConstants.serviceUuid) {
        for (var characteristic in service.characteristics) {
          if (characteristic.uuid.toString().toLowerCase() ==
              BluetoothConstants.characteristicUuid) {
            _statusCharacteristic = characteristic;
            await characteristic.setNotifyValue(true);

            _characteristicSubscription =
                characteristic.lastValueStream.listen((value) {
              if (value.isNotEmpty) {
                final statusStr = String.fromCharCodes(value);
                state = state.copyWith(statusMessage: statusStr);
              }
            });

            state = state.copyWith(statusMessage: 'Ready');
            return;
          }
        }
      }
    }
    state = state.copyWith(
        connectionState: BleConnectionState.error,
        statusMessage: 'Required GATT service not found');
  }

  void _cleanup() {
    _characteristicSubscription?.cancel();
    _statusCharacteristic = null;
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
