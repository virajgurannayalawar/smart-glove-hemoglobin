import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';
import '../providers/scan_session_provider.dart';
import '../providers/patient_provider.dart';
import '../widgets/result_card.dart';

class CheckScanScreen extends ConsumerStatefulWidget {
  const CheckScanScreen({Key? key}) : super(key: key);

  @override
  ConsumerState<CheckScanScreen> createState() => _CheckScanScreenState();
}

class _CheckScanScreenState extends ConsumerState<CheckScanScreen> {
  bool isPregnant = false;

  @override
  Widget build(BuildContext context) {
    final scanState = ref.watch(scanSessionNotifierProvider);
    final patientState = ref.watch(patientNotifierProvider);
    final selectedPatient = patientState.selectedPatient;

    // Validate selected patient exists in current list
    if (selectedPatient != null && 
        !patientState.patients.any((p) => p.id == selectedPatient.id)) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          ref.read(patientNotifierProvider.notifier).clearSelection();
        }
      });
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Hemoglobin Check'),
        elevation: 0,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Patient Details Card (Read-only)
              Card(
                elevation: 2,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Patient Details',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                          fontFamily: 'Poppins',
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          CircleAvatar(
                            radius: 24,
                            backgroundColor: const Color(0xFF0D47A1).withOpacity(0.1),
                            child: Text(
                              selectedPatient?.name.substring(0, 1).toUpperCase() ?? 'P',
                              style: const TextStyle(
                                color: Color(0xFF0D47A1),
                                fontWeight: FontWeight.bold,
                                fontSize: 20,
                              ),
                            ),
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  selectedPatient?.name ?? 'Unknown Patient',
                                  style: const TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                    color: Color(0xFF212121),
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  'Age: ${selectedPatient?.age ?? '-'} • Gender: ${selectedPatient?.gender ?? '-'}',
                                  style: TextStyle(color: Colors.grey[600], fontSize: 13),
                                ),
                                Text(
                                  'ID: ${selectedPatient?.id ?? '-'}',
                                  style: TextStyle(color: Colors.grey[500], fontSize: 11),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // Status Card
              _buildStatusCard(scanState),
              const SizedBox(height: 16),

              // Pregnancy Checkbox (if patient selected)
              if (selectedPatient != null)
                Card(
                  elevation: 1,
                  child: CheckboxListTile(
                    title: const Text('Patient is pregnant'),
                    subtitle: const Text('Affects hemoglobin interpretation'),
                    value: isPregnant,
                    onChanged: (value) {
                      setState(() => isPregnant = value ?? false);
                    },
                  ),
                ),
              const SizedBox(height: 16),

              // Buttons based on scan state
              _buildActionButtons(
                context,
                scanState,
                selectedPatient,
              ),
              const SizedBox(height: 24),

              // Result Card (if success)
              if (scanState.state == ScanSessionState.success &&
                  scanState.result != null)
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Divider(),
                    const SizedBox(height: 16),
                    const Text(
                      'Scan Result',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                    ResultCard(result: scanState.result!),
                    const SizedBox(height: 16),
                    ElevatedButton.icon(
                      onPressed: () {
                        ref
                            .read(scanSessionNotifierProvider.notifier)
                            .resetSession();
                      },
                      icon: const Icon(Icons.check_circle),
                      label: const Text('New Scan'),
                    ),
                  ],
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusCard(ScanSessionNotifierState scanState) {
    final statusColors = {
      ScanSessionState.idle: Colors.grey,
      ScanSessionState.creating: Colors.blue,
      ScanSessionState.polling: Colors.blue,
      ScanSessionState.success: Colors.green,
      ScanSessionState.timeout: Colors.orange,
      ScanSessionState.error: Colors.red,
      ScanSessionState.cancelled: Colors.grey,
    };

    final statusTexts = {
      ScanSessionState.idle: 'Ready',
      ScanSessionState.creating: 'Creating scan session...',
      ScanSessionState.polling: 'Scanning... (attempt ${scanState.pollAttempt})',
      ScanSessionState.success: 'Scan Complete ✓',
      ScanSessionState.timeout: 'Scan Timed Out',
      ScanSessionState.error: 'Error: ${scanState.errorMessage}',
      ScanSessionState.cancelled: 'Cancelled',
    };

    return Card(
      color: statusColors[scanState.state]?.withOpacity(0.1),
      elevation: 1,
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 12,
                  height: 12,
                  decoration: BoxDecoration(
                    color: statusColors[scanState.state],
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    statusTexts[scanState.state] ?? 'Unknown',
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w500,
                      color: statusColors[scanState.state],
                    ),
                  ),
                ),
              ],
            ),
            if (scanState.state == ScanSessionState.polling ||
                scanState.state == ScanSessionState.creating)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    minHeight: 4,
                    backgroundColor: Colors.grey[300],
                    valueColor: AlwaysStoppedAnimation<Color>(
                      statusColors[scanState.state] ?? Colors.blue,
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  void _showScanMethodSelector(BuildContext context, dynamic selectedPatient) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 24.0, horizontal: 16.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Choose Scanning Method',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    fontFamily: 'Poppins',
                    color: Color(0xFF0D47A1),
                  ),
                ),
                const SizedBox(height: 24),
                ElevatedButton.icon(
                  onPressed: () {
                    Navigator.pop(ctx);
                    ref.read(scanSessionNotifierProvider.notifier).startScan(
                          patientId: selectedPatient.id,
                          isPregnant: isPregnant,
                        );
                  },
                  icon: const Icon(Icons.bluetooth),
                  label: const Text('Use Smart Glove (BLE)'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF0D47A1),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: () {
                    Navigator.pop(ctx);
                    _handleCameraScan(context, selectedPatient);
                  },
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('Use Mobile Camera'),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: const Color(0xFF0D47A1),
                    side: const BorderSide(color: Color(0xFF0D47A1)),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Future<void> _handleCameraScan(BuildContext context, dynamic selectedPatient) async {
    try {
      final picker = ImagePicker();
      final photo = await picker.pickImage(
        source: ImageSource.camera,
        imageQuality: 85,
      );
      if (photo == null) return; // Cancelled
      
      final bytes = await photo.readAsBytes();
      
      if (!mounted) return;
      ref.read(scanSessionNotifierProvider.notifier).startScanWithImage(
            patientId: selectedPatient.id,
            isPregnant: isPregnant,
            imageBytes: bytes,
          );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to capture image: $e')),
      );
    }
  }

  Widget _buildActionButtons(
    BuildContext context,
    ScanSessionNotifierState scanState,
    dynamic selectedPatient,
  ) {
    switch (scanState.state) {
      case ScanSessionState.idle:
        return ElevatedButton.icon(
          onPressed: selectedPatient == null
              ? null
              : () => _showScanMethodSelector(context, selectedPatient),
          icon: const Icon(Icons.check_circle_outline),
          label: const Text('Start Scan'),
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
            backgroundColor: Colors.teal,
            disabledBackgroundColor: Colors.grey[300],
          ),
        );

      case ScanSessionState.creating:
      case ScanSessionState.polling:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            ElevatedButton.icon(
              onPressed: () {
                ref.read(scanSessionNotifierProvider.notifier).cancelScan();
              },
              icon: const Icon(Icons.cancel),
              label: const Text('Cancel Scan'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red[400],
              ),
            ),
          ],
        );

      case ScanSessionState.timeout:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Scan timed out. Your hemoglobin reading may still arrive shortly. You can:',
              style: TextStyle(color: Colors.grey[700]),
            ),
            const SizedBox(height: 12),
            ElevatedButton.icon(
              onPressed: () {
                ref.read(scanSessionNotifierProvider.notifier).retryScan();
              },
              icon: const Icon(Icons.refresh),
              label: const Text('Retry Polling'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.orange,
              ),
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: () {
                ref.read(scanSessionNotifierProvider.notifier).resetSession();
              },
              icon: const Icon(Icons.close),
              label: const Text('Start Over'),
            ),
          ],
        );

      case ScanSessionState.error:
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            ElevatedButton.icon(
              onPressed: selectedPatient == null
                  ? null
                  : () => _showScanMethodSelector(context, selectedPatient),
              icon: const Icon(Icons.refresh),
              label: const Text('Retry Scan'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.orange,
              ),
            ),
            const SizedBox(height: 8),
            OutlinedButton.icon(
              onPressed: () {
                ref.read(scanSessionNotifierProvider.notifier).resetSession();
              },
              icon: const Icon(Icons.close),
              label: const Text('Cancel'),
            ),
          ],
        );

      case ScanSessionState.success:
        return ElevatedButton.icon(
          onPressed: () {
            ref.read(scanSessionNotifierProvider.notifier).resetSession();
          },
          icon: const Icon(Icons.check_circle),
          label: const Text('Scan Another Patient'),
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
            backgroundColor: Colors.green,
          ),
        );

      case ScanSessionState.cancelled:
        return ElevatedButton.icon(
          onPressed: () {
            ref.read(scanSessionNotifierProvider.notifier).resetSession();
          },
          icon: const Icon(Icons.check_circle_outline),
          label: const Text('Start New Scan'),
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
            backgroundColor: Colors.teal,
          ),
        );
    }
  }
}
