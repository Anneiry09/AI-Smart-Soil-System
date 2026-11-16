import 'package:flutter_test/flutter_test.dart';
import 'package:smart_soil_app/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const SmartSoilApp());
    expect(find.byType(SmartSoilApp), findsOneWidget);
  });
}
