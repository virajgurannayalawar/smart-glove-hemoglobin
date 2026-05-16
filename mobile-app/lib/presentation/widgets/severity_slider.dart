import 'package:flutter/material.dart';

class SeveritySlider extends StatelessWidget {
  final double hbValue;

  const SeveritySlider({
    super.key,
    required this.hbValue,
  });

  @override
  Widget build(BuildContext context) {
    const double minHb = 0.0;
    const double maxHb = 18.0;

    // Normalize value to prevent overflow
    final clampedValue = hbValue.clamp(minHb, maxHb);
    final percentage = (clampedValue - minHb) / (maxHb - minHb);

    return Column(
      children: [
        LayoutBuilder(
          builder: (context, constraints) {
            final width = constraints.maxWidth;
            final markerPosition = width * percentage;

            return Stack(
              clipBehavior: Clip.none,
              children: [
                // The colored bar
                Container(
                  height: 12,
                  width: double.infinity,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(6),
                    gradient: const LinearGradient(
                      colors: [
                        Colors.red, // < 7
                        Colors.orange, // 7-11
                        Colors.amber, // 11-13
                        Colors.green, // > 13
                      ],
                      stops: [
                        7 / 18,
                        11 / 18,
                        13 / 18,
                        1.0,
                      ],
                    ),
                  ),
                ),
                // The Marker Pin
                Positioned(
                  left: markerPosition - 12, // center the 24px wide pin
                  top: -16,
                  child: Column(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: const Color(0xFF0D47A1), // Navy
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          hbValue.toStringAsFixed(1),
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const Icon(
                        Icons.arrow_drop_down,
                        color: Color(0xFF0D47A1),
                        size: 24,
                      ),
                    ],
                  ),
                ),
              ],
            );
          },
        ),
        const SizedBox(height: 8),
        const Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('Severe', style: TextStyle(fontSize: 10, color: Colors.grey)),
            Text('Normal', style: TextStyle(fontSize: 10, color: Colors.grey)),
          ],
        ),
      ],
    );
  }
}
