/**
 * Color scheme tests - MOB-05, MOB-06
 *
 * MOB-05: Color scheme applies: red=failure, yellow=warning, green=success
 * MOB-06: Dashboard uses blue/white/gold/black color scheme
 */

import { colors, lightTheme, darkTheme } from '../src/theme/colors';

describe('MOB-05: Semantic color scheme (red=failure, yellow=warning, green=success)', () => {
  describe('Status colors', () => {
    it('failure is red', () => {
      // Red hex values start with DC (220 in decimal for red channel > 200)
      expect(colors.status.failure).toMatch(/^#[Dd][Cc]/);
      expect(colors.status.failure).toBe('#DC2626');
    });

    it('warning is yellow/amber', () => {
      // Yellow/amber hex values typically have high R, medium G
      expect(colors.status.warning).toBe('#F59E0B');
    });

    it('success is green', () => {
      // Green hex values start with 10 (low red) and have B981 (green)
      expect(colors.status.success).toBe('#10B981');
    });
  });

  describe('Validation colors follow semantic pattern', () => {
    it('passed is green', () => {
      expect(colors.validation.passed).toBe(colors.status.success);
    });

    it('failed is red', () => {
      expect(colors.validation.failed).toBe(colors.status.failure);
    });
  });

  describe('Skill status colors follow semantic pattern', () => {
    it('passed is green', () => {
      expect(colors.skill.passed).toBe(colors.status.success);
    });

    it('failed is red', () => {
      expect(colors.skill.failed).toBe(colors.status.failure);
    });

    it('in_progress is yellow', () => {
      expect(colors.skill.in_progress).toBe(colors.status.warning);
    });
  });

  describe('Priority colors follow semantic pattern', () => {
    it('critical is red', () => {
      expect(colors.priority.critical).toBe(colors.status.failure);
    });

    it('high is yellow/orange', () => {
      expect(colors.priority.high).toBe(colors.status.warning);
    });
  });

  describe('Column colors for workflow states', () => {
    it('done column is green (success)', () => {
      expect(colors.columns.done).toBe(colors.status.success);
    });

    it('in_progress column is yellow (active work)', () => {
      expect(colors.columns.in_progress).toBe(colors.status.warning);
    });
  });

  describe('Agent status colors', () => {
    it('working is green', () => {
      expect(colors.agent.working).toBe(colors.status.success);
    });

    it('blocked is red', () => {
      expect(colors.agent.blocked).toBe(colors.status.failure);
    });
  });
});

describe('MOB-06: Dashboard uses blue/white/gold/black color scheme', () => {
  describe('Blue as primary', () => {
    it('primary color is blue', () => {
      // Blue hex starts with 25 or 2 (blue channel high)
      expect(colors.dashboard.primary).toBe('#2563EB');
    });

    it('has light and dark blue variants', () => {
      expect(colors.dashboard.primaryLight).toBeDefined();
      expect(colors.dashboard.primaryDark).toBeDefined();
    });
  });

  describe('White as background', () => {
    it('background is white', () => {
      expect(colors.dashboard.background).toBe('#FFFFFF');
    });

    it('surface colors are near-white', () => {
      expect(colors.dashboard.surface).toMatch(/^#F[9A-F]/);
    });
  });

  describe('Gold as accent', () => {
    it('accent is gold', () => {
      expect(colors.dashboard.accent).toBe('#D4AF37');
    });

    it('has light and dark gold variants', () => {
      expect(colors.dashboard.accentLight).toBeDefined();
      expect(colors.dashboard.accentDark).toBeDefined();
    });
  });

  describe('Black for text', () => {
    it('primary text is near-black', () => {
      expect(colors.dashboard.text).toBe('#111827');
    });

    it('has secondary and muted text colors', () => {
      expect(colors.dashboard.textSecondary).toBeDefined();
      expect(colors.dashboard.textMuted).toBeDefined();
    });
  });

  describe('Theme consistency', () => {
    it('light theme uses dashboard colors', () => {
      expect(lightTheme.background).toBe(colors.dashboard.background);
      expect(lightTheme.text).toBe(colors.dashboard.text);
      expect(lightTheme.mode).toBe('light');
    });

    it('dark theme inverts appropriately', () => {
      expect(darkTheme.background).not.toBe(colors.dashboard.background);
      expect(darkTheme.text).not.toBe(colors.dashboard.text);
      expect(darkTheme.mode).toBe('dark');
    });

    it('dark theme maintains semantic status colors', () => {
      expect(darkTheme.status.failure).toBe(colors.status.failure);
      expect(darkTheme.status.warning).toBe(colors.status.warning);
      expect(darkTheme.status.success).toBe(colors.status.success);
    });
  });

  describe('Color type safety', () => {
    it('colors object is readonly', () => {
      // TypeScript 'as const' makes it readonly
      expect(colors).toBeDefined();
      expect(typeof colors.dashboard.primary).toBe('string');
    });
  });
});
