import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { ActivityIndicator, Platform, Text, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { StoreProvider, useStore } from '@/lib/store';
import { useTheme } from '@/lib/theme';

function RootStack() {
  const t = useTheme();
  const { ready } = useStore();

  if (!ready) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: t.bg }}>
        <ActivityIndicator color={t.primary} />
      </View>
    );
  }

  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: t.card },
        headerTintColor: t.primary,
        headerTitleStyle: { color: t.text },
        contentStyle: { backgroundColor: t.bg },
      }}
    >
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="add" options={{ presentation: 'modal', title: 'TESTVERSION · Lebensmittel hinzufügen' }} />
    </Stack>
  );
}

export default function RootLayout() {
  if (Platform.OS === 'web' && typeof window !== 'undefined' &&
      !['localhost', '127.0.0.1', '[::1]'].includes(window.location.hostname)) {
    return <Text>TESTVERSION · Die Expo-Web-App ist nur lokal verfügbar.</Text>;
  }
  return (
    <SafeAreaProvider>
      <StoreProvider>
        <StatusBar style="auto" />
        <RootStack />
      </StoreProvider>
    </SafeAreaProvider>
  );
}
