import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../widgets/result_card.dart';
import '../widgets/history_preview_list.dart';
import '../widgets/patient_selection_list.dart';
import '../providers/auth_provider.dart';
import '../providers/history_provider.dart';
import '../providers/connect_glove_provider.dart';
import '../../core/services/bluetooth_service.dart';
import '../providers/scan_session_provider.dart';
import '../providers/patient_provider.dart';
import '../../domain/entities/scan_result.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authNotifierProvider).user;
    final scanState = ref.watch(scanSessionNotifierProvider);
    final isScanning = scanState.state == ScanSessionState.creating ||
        scanState.state == ScanSessionState.polling;
    final historyState = ref.watch(historyNotifierProvider);
    final bleState = ref.watch(bluetoothServiceProvider);
    final connectGloveState = ref.watch(connectGloveNotifierProvider);
    final patientState = ref.watch(patientNotifierProvider);
    final selectedPatient = patientState.selectedPatient;

    final recentScans = selectedPatient != null
        ? historyState.scans.where((s) => s.patientId == selectedPatient.id).toList()
        : const <ScanResult>[];
    final latestScan = recentScans.isNotEmpty ? recentScans.first : null;

    final bool isDisconnected = bleState.connectionState == BleConnectionState.disconnected || 
                                bleState.connectionState == BleConnectionState.error;

    return Scaffold(
      backgroundColor: Colors.grey[50],
      body: SafeArea(
        child: selectedPatient == null
            ? Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(24.0, 24.0, 24.0, 8.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Welcome Back,',
                          style: TextStyle(color: Colors.grey, fontSize: 14),
                        ),
                        Text(
                          user?.name ?? 'Scanner',
                          style: const TextStyle(
                            fontWeight: FontWeight.bold,
                            fontSize: 22,
                            fontFamily: 'Poppins',
                            color: Color(0xFF0D47A1),
                          ),
                        ),
                        const SizedBox(height: 24),
                        const Text(
                          'Select Patient to Begin',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            fontFamily: 'Poppins',
                          ),
                        ),
                      ],
                    ),
                  ),
                  Expanded(
                    child: PatientSelectionList(
                      onPatientSelected: (patient) {
                        ref.read(patientNotifierProvider.notifier).selectPatient(patient);
                      },
                      onAddPatientPressed: () {
                        context.push('/add-patient').then((result) {
                          if (result == true) {
                            ref.read(patientNotifierProvider.notifier).loadPatients();
                          }
                        });
                      },
                    ),
                  ),
                ],
              )
            : SingleChildScrollView(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Bluetooth Disconnected Banner
                    if (isDisconnected)
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(12),
                        margin: const EdgeInsets.only(bottom: 16),
                        decoration: BoxDecoration(
                          color: Colors.orange.shade100,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.orange),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.bluetooth_disabled, color: Colors.orange),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                bleState.statusMessage,
                                style: const TextStyle(color: Colors.deepOrange, fontWeight: FontWeight.bold),
                              ),
                            ),
                          ],
                        ),
                      ),
                    // Glove Provisioning Status Banner
                    if (!connectGloveState.isProvisioned)
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(12),
                        margin: const EdgeInsets.only(bottom: 16),
                        decoration: BoxDecoration(
                          color: Colors.red.shade100,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.red),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.warning_amber, color: Colors.red.shade700),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'Glove Not Connected',
                                    style: TextStyle(
                                      color: Colors.red,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    'Please provision your glove to begin scanning',
                                    style: TextStyle(color: Colors.red.shade700, fontSize: 12),
                                  ),
                                ],
                              ),
                            ),
                            SizedBox(
                              width: 80,
                              child: ElevatedButton(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.red,
                                  padding: const EdgeInsets.symmetric(horizontal: 8),
                                ),
                                onPressed: () {
                                  context.push('/connect-glove');
                                },
                                child: const Text(
                                  'Connect',
                                  style: TextStyle(fontSize: 12, color: Colors.white),
                                ),
                              ),
                            ),
                          ],
                        ),
                      )
                    else
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(12),
                        margin: const EdgeInsets.only(bottom: 16),
                        decoration: BoxDecoration(
                          color: Colors.green.shade100,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Colors.green),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.check_circle, color: Colors.green),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'Glove Connected',
                                    style: TextStyle(
                                      color: Colors.green,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  Text(
                                    'Ready to scan',
                                    style: TextStyle(color: Colors.green.shade700, fontSize: 12),
                                  ),
                                ],
                              ),
                            ),
                            TextButton(
                              onPressed: () {
                                context.push('/connect-glove');
                              },
                              child: const Text(
                                'Re-provision',
                                style: TextStyle(fontSize: 12),
                              ),
                            ),
                          ],
                        ),
                      ),
                    
                    // Selected Patient Header Row
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            CircleAvatar(
                              radius: 24,
                              backgroundColor: const Color(0xFF0D47A1).withOpacity(0.1),
                              child: Text(
                                selectedPatient.name.substring(0, 1).toUpperCase(),
                                style: const TextStyle(
                                  color: Color(0xFF0D47A1),
                                  fontWeight: FontWeight.bold,
                                  fontSize: 20,
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  selectedPatient.name,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 16,
                                    fontFamily: 'Poppins',
                                  ),
                                ),
                                Text(
                                  'Age: ${selectedPatient.age} • ${selectedPatient.gender}',
                                  style: const TextStyle(color: Colors.grey, fontSize: 12),
                                ),
                              ],
                            ),
                          ],
                        ),
                        IconButton(
                          icon: const Icon(Icons.swap_horiz, color: Color(0xFF0D47A1)),
                          tooltip: 'Change Patient',
                          onPressed: () {
                            ref.read(patientNotifierProvider.notifier).clearSelection();
                          },
                        ),
                      ],
                    ),
                    const SizedBox(height: 32),
                    
                    // Result Card
                    ResultCard(
                      latestResult: latestScan,
                      isScanning: isScanning,
                      onCheckPressed: () {
                        context.push('/check-scan');
                      },
                    ),
                    const SizedBox(height: 32),
                    
                    // History Preview
                    HistoryPreviewList(recentScans: recentScans),
                  ],
                ),
              ),
      ),
    );
  }
}
