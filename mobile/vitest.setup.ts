/**
 * Vitest setup for React Native mobile tests
 */

import { vi } from 'vitest';

// Mock React Native
vi.mock('react-native', () => ({
  View: 'View',
  Text: 'Text',
  TouchableOpacity: 'TouchableOpacity',
  TextInput: 'TextInput',
  FlatList: 'FlatList',
  ScrollView: 'ScrollView',
  RefreshControl: 'RefreshControl',
  Modal: 'Modal',
  Animated: {
    View: 'Animated.View',
    Value: vi.fn(() => ({
      interpolate: vi.fn(() => 0),
    })),
    event: vi.fn(),
    spring: vi.fn(() => ({ start: vi.fn() })),
  },
  Dimensions: {
    get: vi.fn(() => ({ width: 375, height: 812 })),
  },
  StyleSheet: {
    create: (styles: Record<string, unknown>) => styles,
  },
  Platform: {
    OS: 'ios',
    select: (opts: { ios: unknown; android: unknown }) => opts.ios,
  },
}));

// Mock gesture handler
vi.mock('react-native-gesture-handler', () => ({
  PanGestureHandler: 'PanGestureHandler',
  State: {
    END: 5,
    BEGAN: 2,
    ACTIVE: 4,
  },
}));

// Mock AsyncStorage
vi.mock('@react-native-async-storage/async-storage', () => ({
  default: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
    getAllKeys: vi.fn(),
    multiGet: vi.fn(),
    multiSet: vi.fn(),
  },
}));

// Mock testing library
vi.mock('@testing-library/react-native', () => ({
  render: vi.fn((component) => ({
    getByText: vi.fn((text) => ({ children: [text] })),
    getByTestId: vi.fn((id) => ({ testID: id, props: { value: '' } })),
    queryByText: vi.fn(() => null),
    queryByTestId: vi.fn(() => null),
    getAllByText: vi.fn(() => []),
    getByPlaceholderText: vi.fn(() => ({})),
    UNSAFE_root: component,
    queryAllByText: vi.fn(() => []),
  })),
  fireEvent: {
    press: vi.fn(),
    changeText: vi.fn(),
  },
  waitFor: vi.fn((fn) => fn()),
}));

// Global test utilities
global.jest = vi;
