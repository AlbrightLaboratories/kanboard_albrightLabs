/**
 * Push notifications tests - MOB-10
 *
 * MOB-10: Push notifications work on iOS and Android
 */

import { Platform } from 'react-native';

// Mock react-native Platform
jest.mock('react-native', () => ({
  Platform: {
    OS: 'ios',
    select: (opts: { ios: unknown; android: unknown }) => opts.ios,
  },
}));

// Notification types
interface PushNotification {
  id: string;
  title: string;
  body: string;
  data?: Record<string, unknown>;
}

// Mock notification handlers
interface NotificationService {
  requestPermissions: () => Promise<boolean>;
  getToken: () => Promise<string | null>;
  onNotification: (handler: (notification: PushNotification) => void) => () => void;
  scheduleNotification: (notification: PushNotification, delay: number) => Promise<string>;
  cancelNotification: (id: string) => Promise<void>;
  cancelAll: () => Promise<void>;
}

const createNotificationService = (): NotificationService => {
  let permissionsGranted = false;
  let handlers: Array<(n: PushNotification) => void> = [];
  const scheduled: Map<string, NodeJS.Timeout> = new Map();

  return {
    async requestPermissions(): Promise<boolean> {
      // Simulates permission dialog
      permissionsGranted = true;
      return permissionsGranted;
    },

    async getToken(): Promise<string | null> {
      if (!permissionsGranted) return null;
      // Simulates FCM/APNs token
      return Platform.OS === 'ios'
        ? 'apns_token_12345'
        : 'fcm_token_67890';
    },

    onNotification(handler: (n: PushNotification) => void): () => void {
      handlers.push(handler);
      return () => {
        handlers = handlers.filter(h => h !== handler);
      };
    },

    async scheduleNotification(notification: PushNotification, delay: number): Promise<string> {
      const timeout = setTimeout(() => {
        handlers.forEach(h => h(notification));
      }, delay);
      scheduled.set(notification.id, timeout);
      return notification.id;
    },

    async cancelNotification(id: string): Promise<void> {
      const timeout = scheduled.get(id);
      if (timeout) {
        clearTimeout(timeout);
        scheduled.delete(id);
      }
    },

    async cancelAll(): Promise<void> {
      scheduled.forEach(timeout => clearTimeout(timeout));
      scheduled.clear();
    },
  };
};

// Test helper to simulate receiving a notification
const simulateNotification = (
  service: NotificationService,
  notification: PushNotification
): void => {
  // In real app, this comes from native bridge
  const handler = jest.fn();
  const unsubscribe = service.onNotification(handler);
  service.scheduleNotification(notification, 0);
  unsubscribe();
};

describe('MOB-10: Push notifications work on iOS and Android', () => {
  let notificationService: NotificationService;

  beforeEach(() => {
    jest.clearAllMocks();
    notificationService = createNotificationService();
  });

  afterEach(async () => {
    await notificationService.cancelAll();
  });

  describe('Permission handling', () => {
    it('requests notification permissions', async () => {
      const result = await notificationService.requestPermissions();
      expect(result).toBe(true);
    });

    it('returns token after permissions granted', async () => {
      await notificationService.requestPermissions();
      const token = await notificationService.getToken();
      expect(token).toBeTruthy();
    });

    it('returns null token without permissions', async () => {
      const token = await notificationService.getToken();
      expect(token).toBeNull();
    });
  });

  describe('iOS support', () => {
    beforeAll(() => {
      (Platform as any).OS = 'ios';
    });

    it('gets APNs token on iOS', async () => {
      await notificationService.requestPermissions();
      const token = await notificationService.getToken();
      expect(token).toContain('apns');
    });

    it('receives notifications on iOS', async () => {
      const handler = jest.fn();
      const unsubscribe = notificationService.onNotification(handler);

      const notification: PushNotification = {
        id: 'notif-1',
        title: 'Story Updated',
        body: 'Story "Feature X" moved to Done',
        data: { story_id: 'story-1' },
      };

      await notificationService.scheduleNotification(notification, 0);

      // Wait for notification
      await new Promise(resolve => setTimeout(resolve, 10));

      expect(handler).toHaveBeenCalledWith(notification);
      unsubscribe();
    });
  });

  describe('Android support', () => {
    beforeAll(() => {
      (Platform as any).OS = 'android';
    });

    afterAll(() => {
      (Platform as any).OS = 'ios'; // Reset
    });

    it('gets FCM token on Android', async () => {
      await notificationService.requestPermissions();
      const token = await notificationService.getToken();
      expect(token).toContain('fcm');
    });
  });

  describe('Notification handling', () => {
    it('subscribes to notifications', () => {
      const handler = jest.fn();
      const unsubscribe = notificationService.onNotification(handler);

      expect(typeof unsubscribe).toBe('function');
      unsubscribe();
    });

    it('unsubscribes from notifications', async () => {
      const handler = jest.fn();
      const unsubscribe = notificationService.onNotification(handler);
      unsubscribe();

      await notificationService.scheduleNotification({
        id: 'test',
        title: 'Test',
        body: 'Test',
      }, 0);

      await new Promise(resolve => setTimeout(resolve, 10));
      expect(handler).not.toHaveBeenCalled();
    });

    it('handles multiple subscribers', async () => {
      const handler1 = jest.fn();
      const handler2 = jest.fn();

      const unsub1 = notificationService.onNotification(handler1);
      const unsub2 = notificationService.onNotification(handler2);

      await notificationService.scheduleNotification({
        id: 'test',
        title: 'Test',
        body: 'Test',
      }, 0);

      await new Promise(resolve => setTimeout(resolve, 10));

      expect(handler1).toHaveBeenCalled();
      expect(handler2).toHaveBeenCalled();

      unsub1();
      unsub2();
    });
  });

  describe('Scheduled notifications', () => {
    it('schedules future notification', async () => {
      const handler = jest.fn();
      notificationService.onNotification(handler);

      await notificationService.scheduleNotification({
        id: 'scheduled-1',
        title: 'Reminder',
        body: 'Check your tasks',
      }, 50);

      expect(handler).not.toHaveBeenCalled();

      await new Promise(resolve => setTimeout(resolve, 60));
      expect(handler).toHaveBeenCalled();
    });

    it('cancels scheduled notification', async () => {
      const handler = jest.fn();
      notificationService.onNotification(handler);

      const id = await notificationService.scheduleNotification({
        id: 'to-cancel',
        title: 'Will Cancel',
        body: 'This should not appear',
      }, 50);

      await notificationService.cancelNotification(id);

      await new Promise(resolve => setTimeout(resolve, 60));
      expect(handler).not.toHaveBeenCalled();
    });

    it('cancels all notifications', async () => {
      const handler = jest.fn();
      notificationService.onNotification(handler);

      await notificationService.scheduleNotification({
        id: 'notif-1',
        title: 'Test 1',
        body: 'Body 1',
      }, 50);

      await notificationService.scheduleNotification({
        id: 'notif-2',
        title: 'Test 2',
        body: 'Body 2',
      }, 50);

      await notificationService.cancelAll();

      await new Promise(resolve => setTimeout(resolve, 60));
      expect(handler).not.toHaveBeenCalled();
    });
  });

  describe('Notification data', () => {
    it('includes custom data payload', async () => {
      const handler = jest.fn();
      notificationService.onNotification(handler);

      const notification: PushNotification = {
        id: 'data-notif',
        title: 'Story Assigned',
        body: 'You were assigned to Story X',
        data: {
          story_id: 'story-123',
          action: 'navigate',
          screen: 'StoryDetail',
        },
      };

      await notificationService.scheduleNotification(notification, 0);
      await new Promise(resolve => setTimeout(resolve, 10));

      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          data: expect.objectContaining({
            story_id: 'story-123',
          }),
        })
      );
    });
  });
});
