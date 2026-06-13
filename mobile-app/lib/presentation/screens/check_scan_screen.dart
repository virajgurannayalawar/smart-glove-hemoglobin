import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
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
              // Patient Selection Card
              Card(
                elevation: 2,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Select Patient',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 12),
                      if (patientState.isLoading)
                        const Center(
                          child: CircularProgressIndicator(),
                        )
                      else if (patientState.patients.isEmpty)
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: Colors.grey[100],
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Column(
                            children: [
                              Icon(Icons.person_add, color: Colors.grey[400]),
                              const SizedBox(height: 8),
                              Text(
                                'No patients found',
                                style: TextStyle(color: Colors.grey[600]),
                              ),
                              const SizedBox(height: 12),
                              ElevatedButton.icon(
                                onPressed: () {
                                  context.go('/patients');
                                },
                                icon: const Icon(Icons.add),
                                label: const Text('Add Patient'),
                              ),
                            ],
                          ),
                        )
                      else
                        DropdownButton<String>(
                          value: selectedPatient?.id,
                          isExpanded: true,
                          hint: const Text('Choose a patient'),
                          items: patientState.patients.map((patient) {
                            return DropdownMenuItem(
                              value: patient.id,
                              child: Text('${patient.name} (${patient.age}y)'),
                            );
                          }).toList(),
                          onChanged: (patientId) {
                            if (patientId != null) {
                              final patient = patientState.patients
                                  .firstWhere((p) => p.id == patientId);
                              ref
                                  .read(patientNotifierProvider.notifier)
                                  .selectPatient(patient);
                            }
                          },
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
              : () {
                  ref.read(scanSessionNotifierProvider.notifier).startScan(
                        patientId: selectedPatient.id,
                        isPregnant: isPregnant,
                      );
                },
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
                  : () {
                      ref.read(scanSessionNotifierProvider.notifier).startScan(
                            patientId: selectedPatient.id,
                            isPregnant: isPregnant,
                          );
                    },
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
