/**
 * Kanboard AlbrightLabs Color Scheme
 *
 * Semantic Colors:
 * - Red: Failure, serious event warning, loss of money
 * - Yellow: Warning that may or may not impact performance
 * - Green: Money making, everything is working, success
 *
 * Dashboard Colors:
 * - Blue: Primary brand color
 * - White: Background and text
 * - Gold: Accent and highlights
 * - Black: Text and borders
 */

export const colors = {
  // Semantic Status Colors
  status: {
    failure: '#DC2626',      // Red - failure, serious warning, money loss
    failureLight: '#FEE2E2', // Light red for backgrounds
    failureDark: '#991B1B',  // Dark red for emphasis

    warning: '#F59E0B',      // Yellow - warning, may impact performance
    warningLight: '#FEF3C7', // Light yellow for backgrounds
    warningDark: '#B45309',  // Dark yellow for emphasis

    success: '#10B981',      // Green - success, money making, working
    successLight: '#D1FAE5', // Light green for backgrounds
    successDark: '#047857',  // Dark green for emphasis
  },

  // Dashboard Brand Colors
  dashboard: {
    primary: '#2563EB',      // Blue - primary brand
    primaryLight: '#DBEAFE', // Light blue for backgrounds
    primaryDark: '#1D4ED8',  // Dark blue for emphasis

    background: '#FFFFFF',   // White - primary background
    surface: '#F9FAFB',      // Off-white - card backgrounds
    surfaceAlt: '#F3F4F6',   // Alternate surface

    accent: '#D4AF37',       // Gold - accent and highlights
    accentLight: '#F5E6B0',  // Light gold
    accentDark: '#A68A2E',   // Dark gold

    text: '#111827',         // Black - primary text
    textSecondary: '#4B5563', // Gray - secondary text
    textMuted: '#9CA3AF',    // Light gray - muted text
    border: '#E5E7EB',       // Light gray - borders
    borderDark: '#374151',   // Dark gray - dark borders
  },

  // Column-specific colors (semantic)
  columns: {
    backlog: '#9CA3AF',      // Gray - not started
    groomed: '#3B82F6',      // Blue - refined
    in_progress: '#F59E0B',  // Yellow/Amber - active work
    validation: '#8B5CF6',   // Purple - testing
    done: '#10B981',         // Green - completed
  },

  // Priority colors
  priority: {
    critical: '#DC2626',     // Red
    high: '#F59E0B',         // Orange/Yellow
    medium: '#3B82F6',       // Blue
    low: '#6B7280',          // Gray
  },

  // Agent/Worker status colors
  agent: {
    idle: '#9CA3AF',         // Gray
    working: '#10B981',      // Green
    validating: '#8B5CF6',   // Purple
    blocked: '#DC2626',      // Red
    offline: '#374151',      // Dark gray
  },

  // Skill status colors
  skill: {
    pending: '#9CA3AF',      // Gray
    in_progress: '#F59E0B',  // Yellow
    passed: '#10B981',       // Green
    failed: '#DC2626',       // Red
  },

  // Validation colors
  validation: {
    passed: '#10B981',       // Green
    failed: '#DC2626',       // Red
    running: '#3B82F6',      // Blue
    pending: '#9CA3AF',      // Gray
  },
} as const;

// Type for accessing colors
export type Colors = typeof colors;

// Light theme (default)
export const lightTheme = {
  ...colors,
  mode: 'light' as const,
  background: colors.dashboard.background,
  surface: colors.dashboard.surface,
  text: colors.dashboard.text,
  textSecondary: colors.dashboard.textSecondary,
  border: colors.dashboard.border,
};

// Dark theme
export const darkTheme = {
  ...colors,
  mode: 'dark' as const,
  background: '#111827',
  surface: '#1F2937',
  text: '#F9FAFB',
  textSecondary: '#D1D5DB',
  border: '#374151',
  dashboard: {
    ...colors.dashboard,
    background: '#111827',
    surface: '#1F2937',
    surfaceAlt: '#374151',
    text: '#F9FAFB',
    textSecondary: '#D1D5DB',
    textMuted: '#6B7280',
    border: '#374151',
    borderDark: '#4B5563',
  },
};

export type Theme = typeof lightTheme | typeof darkTheme;
