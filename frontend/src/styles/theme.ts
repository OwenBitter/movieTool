import type { ThemeConfig } from 'antd';

export type ThemeMode = 'dark' | 'light';

const baseTokens = {
  borderRadius: 8,
  borderRadiusLG: 12,
  borderRadiusSM: 4,
  fontSize: 14,
  fontSizeLG: 16,
  fontSizeSM: 12,
  fontFamily: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif`,
  lineHeight: 1.5715,
};

export const cinemaNoirTheme: ThemeConfig = {
  token: {
    colorBgBase: '#08080c',
    colorBgContainer: '#181822',
    colorBgElevated: '#242433',
    colorBgLayout: '#08080c',
    colorText: '#e8e8ee',
    colorTextSecondary: '#88889a',
    colorTextTertiary: '#666678',
    colorTextQuaternary: '#4a4a58',
    colorPrimary: '#e8b84b',
    colorPrimaryHover: '#f5d06b',
    colorPrimaryActive: '#d4a63a',
    colorBorder: 'rgba(255,255,255,0.05)',
    colorBorderSecondary: 'rgba(255,255,255,0.08)',
    colorSuccess: '#2ecc71',
    colorError: '#c0392b',
    colorWarning: '#e8b84b',
    colorInfo: '#3b82f6',
    ...baseTokens,
    boxShadow: '0 4px 24px rgba(0,0,0,0.4)',
    boxShadowSecondary: '0 2px 8px rgba(0,0,0,0.3)',
  },
  components: {
    Layout: {
      siderBg: '#0f0f16',
      headerBg: '#0f0f16',
      bodyBg: '#08080c',
      triggerBg: '#242433',
      triggerColor: '#e8e8ee',
    },
    Menu: {
      darkItemBg: '#0f0f16',
      darkItemSelectedBg: '#242433',
      darkItemHoverBg: '#242433',
      darkItemColor: '#e8e8ee',
      darkItemSelectedColor: '#e8b84b',
    },
    Table: {
      headerBg: '#181822',
      headerColor: '#88889a',
      rowHoverBg: 'rgba(232,184,75,0.08)',
      borderColor: 'rgba(255,255,255,0.05)',
      cellPaddingBlock: 10,
      cellPaddingInline: 16,
    },
    Card: {
      colorBgContainer: '#181822',
      paddingLG: 16,
    },
    Modal: {
      colorBgElevated: '#181822',
      headerBg: '#181822',
      contentBg: '#181822',
      titleColor: '#e8e8ee',
    },
    Tag: {
      defaultBg: '#2a2a3a',
      defaultColor: '#e8e8ee',
    },
    Button: {
      defaultBg: '#242433',
      defaultBorderColor: 'rgba(255,255,255,0.08)',
      defaultColor: '#e8e8ee',
      defaultHoverBg: '#2a2a3a',
      defaultHoverBorderColor: 'rgba(255,255,255,0.12)',
      defaultHoverColor: '#e8b84b',
    },
    Input: {
      colorBgContainer: '#181822',
      colorBorder: 'rgba(255,255,255,0.05)',
      colorTextPlaceholder: '#4a4a58',
      activeBorderColor: '#e8b84b',
      hoverBorderColor: 'rgba(255,255,255,0.1)',
    },
    Select: {
      colorBgElevated: '#242433',
      optionSelectedBg: 'rgba(232,184,75,0.15)',
      optionActiveBg: 'rgba(232,184,75,0.08)',
    },
    Popover: {
      colorBgElevated: '#242433',
    },
    Message: {
      colorBgElevated: '#242433',
      contentBg: '#242433',
    },
    Rate: {
      starColor: '#e8b84b',
      starSize: 18,
    },
  },
};

export const lightTheme: ThemeConfig = {
  token: {
    ...baseTokens,
    colorBgBase: '#ffffff',
    colorBgContainer: '#ffffff',
    colorBgElevated: '#ffffff',
    colorBgLayout: '#f5f5f5',
    colorText: '#1a1a2e',
    colorTextSecondary: '#666678',
    colorTextTertiary: '#88889a',
    colorPrimary: '#d4a63a',
    colorPrimaryHover: '#c0902e',
    colorPrimaryActive: '#b0802a',
    colorBorder: 'rgba(0,0,0,0.08)',
    colorBorderSecondary: 'rgba(0,0,0,0.06)',
    colorSuccess: '#27ae60',
    colorError: '#c0392b',
    colorWarning: '#e67e22',
    colorInfo: '#2980b9',
    boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
    boxShadowSecondary: '0 2px 8px rgba(0,0,0,0.06)',
  },
  components: {
    Layout: {
      siderBg: '#fafafa',
      headerBg: '#ffffff',
      bodyBg: '#f5f5f5',
    },
    Menu: {
      darkItemBg: '#fafafa',
      darkItemSelectedBg: '#f0f0f0',
      darkItemHoverBg: '#f0f0f0',
      darkItemColor: '#1a1a2e',
      darkItemSelectedColor: '#d4a63a',
    },
    Table: {
      headerBg: '#fafafa',
      headerColor: '#666678',
      rowHoverBg: 'rgba(212,166,58,0.05)',
      borderColor: 'rgba(0,0,0,0.06)',
    },
    Card: {
      colorBgContainer: '#ffffff',
    },
    Modal: {
      colorBgElevated: '#ffffff',
      headerBg: '#ffffff',
      contentBg: '#ffffff',
      titleColor: '#1a1a2e',
    },
    Tag: {
      defaultBg: '#f0f0f0',
      defaultColor: '#555',
    },
    Button: {
      defaultBg: '#ffffff',
      defaultBorderColor: 'rgba(0,0,0,0.12)',
      defaultColor: '#1a1a2e',
      defaultHoverBg: '#fafafa',
      defaultHoverBorderColor: 'rgba(0,0,0,0.18)',
      defaultHoverColor: '#d4a63a',
    },
    Input: {
      colorBgContainer: '#ffffff',
      colorBorder: 'rgba(0,0,0,0.10)',
      colorTextPlaceholder: '#aaa',
      activeBorderColor: '#d4a63a',
      hoverBorderColor: 'rgba(0,0,0,0.18)',
    },
    Select: {
      colorBgElevated: '#ffffff',
      optionSelectedBg: 'rgba(212,166,58,0.10)',
      optionActiveBg: 'rgba(212,166,58,0.05)',
    },
    Rate: {
      starColor: '#d4a63a',
      starSize: 18,
    },
  },
};

export function getTheme(mode: ThemeMode): ThemeConfig {
  return mode === 'light' ? lightTheme : cinemaNoirTheme;
}
