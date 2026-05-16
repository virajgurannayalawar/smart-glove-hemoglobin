import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../widgets/result_card.dart';
import '../widgets/history_preview_list.dart';
import '../providers/auth_provider.dart';
import '../providers/history_provider.dart';
import '../../core/services/bluetooth_service.dart';

// Dummy provider for scan status until Step 9
final isScanningProvider = StateProvider<bool>((ref) => false);

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authNotifierProvider).user;
    final isScanning = ref.watch(isScanningProvider);
    final historyState = ref.watch(historyNotifierProvider);
    final bleState = ref.watch(bluetoothServiceProvider);
    final recentScans = historyState.scans;
    final latestScan = recentScans.isNotEmpty ? recentScans.first : null;

    final bool isDisconnected = bleState.connectionState == BleConnectionState.disconnected || 
                                bleState.connectionState == BleConnectionState.error;

    return Scaffold(
      backgroundColor: Colors.grey[50],
      body: SafeArea(
        child: SingleChildScrollView(
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
              // Header Row
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 24,
                        backgroundColor: const Color(0xFF0D47A1).withOpacity(0.1),
                        child: Text(
                          user?.name.substring(0, 1).toUpperCase() ?? 'P',
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
                            user?.name ?? 'Unknown Patient',
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                              fontFamily: 'Poppins',
                            ),
                          ),
                          Text(
                            'ID: ${user?.patientId ?? '-'} • ${user?.age ?? '-'} / ${user?.gender ?? '-'}',
                            style: const TextStyle(color: Colors.grey, fontSize: 12),
                          ),
                        ],
                      ),
                    ],
                  ),
                  Row(
                    children: [
                      // Bluetooth/Cloud sync status icon
                      Icon(
                        isDisconnected ? Icons.bluetooth_disabled : Icons.bluetooth_connected,
                        color: isDisconnected ? Colors.grey : Colors.blue,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        bleState.statusMessage,
                        style: TextStyle(
                          fontSize: 10,
                          color: isDisconnected ? Colors.grey : Colors.blue,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(width: 16),
                      const Icon(Icons.cloud_done, color: Colors.green),
                      const SizedBox(width: 16),
                      IconButton(
                        icon: const Icon(Icons.menu),
                        onPressed: () {
                          // Hamburger menu action
                        },
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 32),
              
              // Result Card
              ResultCard(
                latestResult: latestScan,
                isScanning: isScanning,
                onCheckPressed: () {
                  ref.read(isScanningProvider.notifier).state = true;
                  // Simulate scan delay
                  Future.delayed(const Duration(seconds: 2), () {
                    if (context.mounted) {
                      ref.read(isScanningProvider.notifier).state = false;
                    }
                  });
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
