import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart' as fbp;
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../presentation/providers/connect_glove_provider.dart';

class ConnectGloveScreen extends ConsumerStatefulWidget {
  const ConnectGloveScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<ConnectGloveScreen> createState() => _ConnectGloveScreenState();
}

class _ConnectGloveScreenState extends ConsumerState<ConnectGloveScreen> {
  final _wifiSsidController = TextEditingController();
  final _wifiPasswordController = TextEditingController();
  bool _showWifiPassword = false;

  @override
  void initState() {
    super.initState();
    // Auto-start scanning when screen loads
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(connectGloveNotifierProvider.notifier).startScan();
    });
  }

  @override
  void dispose() {
    _wifiSsidController.dispose();
    _wifiPasswordController.dispose();
    super.dispose();
  }

  void _handleDeviceSelected(fbp.BluetoothDevice device) async {
    final notifier = ref.read(connectGloveNotifierProvider.notifier);
    
    // Show provisioning modal
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => _ProvisioningDialog(
        device: device,
        wifiSsid: _wifiSsidController.text,
        wifiPassword: _wifiPasswordController.text,
        onComplete: () {
          Navigator.pop(ctx);
          // Navigate back with success
          Navigator.pop(context, true);
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(connectGloveNotifierProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Connect Smart Glove'),
        elevation: 0,
      ),
      body: state.state == ProvisioningState.provisioning ||
              state.state == ProvisioningState.success ||
              state.state == ProvisioningState.connecting
          ? const SizedBox() // Dialog handles these states
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Status card
                  _buildStatusCard(state),
                  const SizedBox(height: 24),

                  // Step 1: Device selection
                  _buildStepCard(
                    stepNumber: '1',
                    title: 'Select Glove Device',
                    child: _buildDeviceList(state),
                  ),
                  const SizedBox(height: 20),

                  // Step 2: Wi-Fi credentials (only if device selected)
                  if (state.selectedDevice != null)
                    _buildStepCard(
                      stepNumber: '2',
                      title: 'Enter Wi-Fi Credentials',
                      child: _buildWifiForm(state),
                    ),
                  const SizedBox(height: 20),

                  // Step 3: Provision button (only if device selected and wifi filled)
                  if (state.selectedDevice != null &&
                      _wifiSsidController.text.isNotEmpty &&
                      _wifiPasswordController.text.isNotEmpty)
                    _buildProvisionButton(state),
                ],
              ),
            ),
    );
  }

  Widget _buildStatusCard(ConnectGloveState state) {
    Color? bgColor;
    IconData? icon;
    String title = '';
    String subtitle = state.statusMessage;

    switch (state.state) {
      case ProvisioningState.idle:
        bgColor = Colors.blue.shade50;
        icon = Icons.info_outline;
        title = 'Ready to Connect';
        break;
      case ProvisioningState.scanning:
        bgColor = Colors.blue.shade50;
        icon = Icons.bluetooth_searching;
        title = 'Scanning...';
        break;
      case ProvisioningState.connecting:
        bgColor = Colors.orange.shade50;
        icon = Icons.bluetooth_connected;
        title = 'Connecting...';
        break;
      case ProvisioningState.provisioning:
        bgColor = Colors.orange.shade50;
        icon = Icons.sync;
        title = 'Provisioning...';
        break;
      case ProvisioningState.success:
        bgColor = Colors.green.shade50;
        icon = Icons.check_circle;
        title = 'Success!';
        break;
      case ProvisioningState.error:
        bgColor = Colors.red.shade50;
        icon = Icons.error_outline;
        title = 'Error';
        break;
      case ProvisioningState.fetchingCredentials:
        bgColor = Colors.blue.shade50;
        icon = Icons.downloading;
        title = 'Fetching Credentials...';
        break;
    }

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: (bgColor?.withOpacity(0.3) ?? Colors.grey),
        ),
      ),
      child: Row(
        children: [
          Icon(icon, size: 28),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStepCard({
    required String stepNumber,
    required String title,
    required Widget child,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade300),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: Colors.blue,
                  borderRadius: BorderRadius.circular(50),
                ),
                child: Center(
                  child: Text(
                    stepNumber,
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          child,
        ],
      ),
    );
  }

  Widget _buildDeviceList(ConnectGloveState state) {
    if (state.availableDevices.isEmpty) {
      return Center(
        child: Column(
          children: [
            Icon(Icons.bluetooth_disabled, size: 48, color: Colors.grey),
            const SizedBox(height: 8),
            const Text('No devices found. Make sure Bluetooth is on.'),
          ],
        ),
      );
    }

    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: state.availableDevices.length,
      itemBuilder: (ctx, idx) {
        final device = state.availableDevices[idx];
        final isSelected = state.selectedDevice?.id == device.device.id;

        return GestureDetector(
          onTap: () => _handleDeviceSelected(device.device),
          child: Container(
            margin: const EdgeInsets.symmetric(vertical: 8),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              border: Border.all(
                color: isSelected ? Colors.blue : Colors.grey.shade300,
                width: isSelected ? 2 : 1,
              ),
              borderRadius: BorderRadius.circular(8),
              color: isSelected ? Colors.blue.shade50 : Colors.transparent,
            ),
            child: Row(
              children: [
                Icon(
                  Icons.bluetooth,
                  color: isSelected ? Colors.blue : Colors.grey,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        device.device.advName.isNotEmpty
                            ? device.device.advName
                            : 'Unknown Device',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      Text(
                        device.device.id.toString(),
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                if (isSelected)
                  const Icon(Icons.check_circle, color: Colors.blue),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildWifiForm(ConnectGloveState state) {
    return Column(
      children: [
        TextField(
          controller: _wifiSsidController,
          decoration: InputDecoration(
            labelText: 'Wi-Fi SSID',
            hintText: 'Enter your network name',
            prefixIcon: const Icon(Icons.wifi),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          enabled: state.state == ProvisioningState.idle,
        ),
        const SizedBox(height: 16),
        TextField(
          controller: _wifiPasswordController,
          decoration: InputDecoration(
            labelText: 'Wi-Fi Password',
            hintText: 'Enter your network password',
            prefixIcon: const Icon(Icons.lock),
            suffixIcon: IconButton(
              icon: Icon(
                _showWifiPassword ? Icons.visibility_off : Icons.visibility,
              ),
              onPressed: () {
                setState(() {
                  _showWifiPassword = !_showWifiPassword;
                });
              },
            ),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          obscureText: !_showWifiPassword,
          enabled: state.state == ProvisioningState.idle,
        ),
        const SizedBox(height: 8),
        Align(
          alignment: Alignment.centerLeft,
          child: Text(
            '⚠️ Password is not stored on device',
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.orange.shade700,
                ),
          ),
        ),
      ],
    );
  }

  Widget _buildProvisionButton(ConnectGloveState state) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        onPressed: state.state == ProvisioningState.idle
            ? () => _handleDeviceSelected(state.selectedDevice!)
            : null,
        style: ElevatedButton.styleFrom(
          padding: const EdgeInsets.symmetric(vertical: 16),
          backgroundColor: Colors.green,
          disabledBackgroundColor: Colors.grey,
        ),
        child: const Text(
          'Provision Glove',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: Colors.white,
          ),
        ),
      ),
    );
  }
}

/// Dialog that shows provisioning progress
class _ProvisioningDialog extends ConsumerStatefulWidget {
  final fbp.BluetoothDevice device;
  final String wifiSsid;
  final String wifiPassword;
  final VoidCallback onComplete;

  const _ProvisioningDialog({
    required this.device,
    required this.wifiSsid,
    required this.wifiPassword,
    required this.onComplete,
    Key? key,
  }) : super(key: key);

  @override
  ConsumerState<_ProvisioningDialog> createState() =>
      _ProvisioningDialogState();
}

class _ProvisioningDialogState extends ConsumerState<_ProvisioningDialog> {
  @override
  void initState() {
    super.initState();
    _startProvisioning();
  }

  Future<void> _startProvisioning() async {
    final notifier = ref.read(connectGloveNotifierProvider.notifier);
    final success = await notifier.completeProvisioning(
      device: widget.device,
      wifiSsid: widget.wifiSsid,
      wifiPassword: widget.wifiPassword,
    );

    if (!mounted) return;

    if (success) {
      // Show success for 2 seconds, then call onComplete
      await Future.delayed(const Duration(seconds: 2));
      if (mounted) {
        widget.onComplete();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(connectGloveNotifierProvider);

    return Dialog(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (state.state == ProvisioningState.success)
              Icon(
                Icons.check_circle,
                size: 64,
                color: Colors.green.shade600,
              )
            else if (state.state == ProvisioningState.error)
              Icon(
                Icons.error_outline,
                size: 64,
                color: Colors.red.shade600,
              )
            else
              const CircularProgressIndicator(),
            const SizedBox(height: 16),
            Text(
              state.statusMessage,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            if (state.errorMessage != null) ...[
              const SizedBox(height: 8),
              Text(
                state.errorMessage!,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.red,
                    ),
              ),
            ],
            const SizedBox(height: 24),
            if (state.state == ProvisioningState.error)
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(context),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                  ),
                  child: const Text('Back'),
                ),
              )
            else if (state.state == ProvisioningState.success)
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: widget.onComplete,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                  ),
                  child: const Text('Done'),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
