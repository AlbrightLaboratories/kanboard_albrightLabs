/**
 * Vitest setup for React Native mobile tests
 *
 * Uses a simplified mock approach that avoids react-test-renderer compatibility issues.
 */

import { vi } from 'vitest';

// Mock React Native components as strings
vi.mock('react-native', () => ({
  View: 'View',
  Text: 'Text',
  TouchableOpacity: 'TouchableOpacity',
  TouchableWithoutFeedback: 'TouchableWithoutFeedback',
  Pressable: 'Pressable',
  TextInput: 'TextInput',
  FlatList: 'FlatList',
  ScrollView: 'ScrollView',
  RefreshControl: 'RefreshControl',
  Modal: 'Modal',
  Image: 'Image',
  KeyboardAvoidingView: 'KeyboardAvoidingView',
  SafeAreaView: 'SafeAreaView',
  ActivityIndicator: 'ActivityIndicator',
  Switch: 'Switch',
  StatusBar: 'StatusBar',
  Keyboard: {
    dismiss: vi.fn(),
    addListener: vi.fn(() => ({ remove: vi.fn() })),
  },
  Animated: {
    View: 'Animated.View',
    Text: 'Animated.Text',
    Image: 'Animated.Image',
    ScrollView: 'Animated.ScrollView',
    FlatList: 'Animated.FlatList',
    Value: vi.fn(() => ({
      interpolate: vi.fn(() => 0),
      setValue: vi.fn(),
    })),
    event: vi.fn(),
    spring: vi.fn(() => ({ start: vi.fn() })),
    timing: vi.fn(() => ({ start: vi.fn() })),
    sequence: vi.fn(() => ({ start: vi.fn() })),
    parallel: vi.fn(() => ({ start: vi.fn() })),
  },
  Dimensions: {
    get: vi.fn(() => ({ width: 375, height: 812 })),
    addEventListener: vi.fn(() => ({ remove: vi.fn() })),
  },
  StyleSheet: {
    create: (styles: any) => styles,
    flatten: (style: any) => style,
  },
  Platform: {
    OS: 'ios',
    select: (opts: any) => opts.ios,
  },
  PixelRatio: {
    get: vi.fn(() => 2),
    roundToNearestPixel: vi.fn((n: number) => n),
  },
  Alert: {
    alert: vi.fn(),
  },
  Linking: {
    openURL: vi.fn(),
    canOpenURL: vi.fn(() => Promise.resolve(true)),
  },
  AppState: {
    currentState: 'active',
    addEventListener: vi.fn(() => ({ remove: vi.fn() })),
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

// Track component instances for fireEvent
const componentRegistry = new Map<string, any>();

// Mock @testing-library/react-native with simplified approach
vi.mock('@testing-library/react-native', () => {
  const mockRender = vi.fn((component: any) => {
    // Store component props for callback testing
    const extractProps = (node: any, registry: Map<string, any>): void => {
      if (!node || typeof node !== 'object') return;

      const props = node.props || {};
      const testID = props.testID;

      if (testID) {
        registry.set(testID, { props, type: node.type });
      }

      // Process children
      const children = props.children;
      if (Array.isArray(children)) {
        children.forEach((child: any) => extractProps(child, registry));
      } else if (children && typeof children === 'object') {
        extractProps(children, registry);
      }
    };

    componentRegistry.clear();
    extractProps(component, componentRegistry);

    return {
      getByTestId: vi.fn((id: string) => {
        const stored = componentRegistry.get(id);
        if (stored) {
          return { props: stored.props, type: stored.type, testID: id };
        }
        return { props: {}, testID: id };
      }),
      queryByTestId: vi.fn((id: string) => {
        const stored = componentRegistry.get(id);
        return stored ? { props: stored.props, type: stored.type, testID: id } : null;
      }),
      getByText: vi.fn((text: string) => ({ props: { children: text }, text })),
      queryByText: vi.fn(() => null),
      getAllByText: vi.fn(() => []),
      queryAllByText: vi.fn(() => []),
      getByPlaceholderText: vi.fn((placeholder: string) => ({ props: { placeholder } })),
      UNSAFE_root: component,
    };
  });

  const mockFireEvent = Object.assign(
    vi.fn((element: any, eventName: string, eventData?: any) => {
      const propName = `on${eventName.charAt(0).toUpperCase()}${eventName.slice(1)}`;
      const handler = element?.props?.[propName];
      if (typeof handler === 'function') {
        handler(eventData);
      }
    }),
    {
      press: vi.fn((element: any) => {
        const handler = element?.props?.onPress;
        if (typeof handler === 'function') {
          handler();
        }
      }),
      changeText: vi.fn((element: any, text: string) => {
        const handler = element?.props?.onChangeText;
        if (typeof handler === 'function') {
          handler(text);
        }
      }),
      blur: vi.fn((element: any) => {
        const handler = element?.props?.onBlur;
        if (typeof handler === 'function') {
          handler();
        }
      }),
    }
  );

  return {
    render: mockRender,
    fireEvent: mockFireEvent,
    waitFor: vi.fn(async (callback: () => any) => callback()),
    act: vi.fn((callback: () => any) => callback()),
  };
});

// Global test utilities
(global as any).jest = vi;
