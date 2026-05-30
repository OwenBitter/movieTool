import type { ThemeConfig } from 'antd';

export type ThemeMode = 'dark' | 'light';

const baseTokens = {
  borderRadius: 18,
  borderRadiusLG: 24,
  borderRadiusSM: 16,
  fontSize: 14,
  fontSizeLG: 16,
  fontSizeSM: 12,
  fontFamily: `Nunito, "Noto Sans SC", "PingFang SC", "Microsoft YaHei", -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`,
  lineHeight: 1.5715,
};

export const cinemaNoirTheme: ThemeConfig = {
  token: {
    colorBgBase: '#08080c',
    colorBgContainer: '#181822',
    colorBgElevated: '#242433',
    colorBgLayout: '#08080c',
    colorText: '#e8e8ee',
    colorTextSecondary: '#9f927d',
    colorTextTertiary: '#666678',
    colorTextQuaternary: '#4a4a58',
    colorPrimary: '#19c8b9',
    colorPrimaryHover: '#3dd4c6',
    colorPrimaryActive: '#50B9AB',
    colorBorder: 'rgba(255,255,255,0.05)',
    colorBorderSecondary: 'rgba(255,255,255,0.08)',
    colorSuccess: '#6fba2c',
    colorError: '#e05a5a',
    colorWarning: '#f5c31c',
    colorInfo: '#19c8b9',
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
      darkItemSelectedColor: '#19c8b9',
    },
    Table: {
      headerBg: '#181822',
      headerColor: '#88889a',
      rowHoverBg: 'rgba(25,200,185,0.08)',
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
      defaultHoverColor: '#19c8b9',
    },
    Input: {
      colorBgContainer: '#181822',
      colorBorder: 'rgba(255,255,255,0.05)',
      colorTextPlaceholder: '#4a4a58',
      activeBorderColor: '#19c8b9',
      hoverBorderColor: 'rgba(255,255,255,0.1)',
    },
    Select: {
      colorBgElevated: '#242433',
      optionSelectedBg: 'rgba(25,200,185,0.15)',
      optionActiveBg: 'rgba(25,200,185,0.08)',
    },
    Popover: {
      colorBgElevated: '#242433',
    },
    Message: {
      colorBgElevated: '#242433',
      contentBg: '#242433',
    },
    Rate: {
      starColor: '#f5c31c',
      starSize: 18,
    },
  },
};

export const lightTheme: ThemeConfig = {
  token: {
    ...baseTokens,
    colorBgBase: '#f8f8f0',
    colorBgContainer: '#ffffff',
    colorBgElevated: '#ffffff',
    colorBgLayout: '#f0e8d8',
    colorText: '#794f27',
    colorTextSecondary: '#9f927d',
    colorTextTertiary: '#c4b89e',
    colorPrimary: '#19c8b9',
    colorPrimaryHover: '#3dd4c6',
    colorPrimaryActive: '#50B9AB',
    colorBorder: 'rgba(0,0,0,0.08)',
    colorBorderSecondary: 'rgba(0,0,0,0.06)',
    colorSuccess: '#6fba2c',
    colorError: '#e05a5a',
    colorWarning: '#f5c31c',
    colorInfo: '#19c8b9',
    boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
    boxShadowSecondary: '0 2px 8px rgba(0,0,0,0.06)',
  },
  components: {
    Layout: {
      siderBg: '#f0e8d8',
      headerBg: '#ffffff',
      bodyBg: '#f0e8d8',
    },
    Menu: {
      darkItemBg: '#e8ddd0',
      darkItemSelectedBg: '#d6c9b8',
      darkItemHoverBg: '#d6c9b8',
      darkItemColor: '#794f27',
      darkItemSelectedColor: '#19c8b9',
    },
    Table: {
      headerBg: '#f0e8d8',
      headerColor: '#9f927d',
      rowHoverBg: 'rgba(25,200,185,0.05)',
      borderColor: 'rgba(0,0,0,0.06)',
    },
    Card: {
      colorBgContainer: '#ffffff',
    },
    Modal: {
      colorBgElevated: '#ffffff',
      headerBg: '#ffffff',
      contentBg: '#ffffff',
      titleColor: '#794f27',
    },
    Tag: {
      defaultBg: '#f0e8d8',
      defaultColor: '#794f27',
    },
    Button: {
      defaultBg: '#ffffff',
      defaultBorderColor: 'rgba(0,0,0,0.12)',
      defaultColor: '#794f27',
      defaultHoverBg: '#fafafa',
      defaultHoverBorderColor: 'rgba(0,0,0,0.18)',
      defaultHoverColor: '#19c8b9',
    },
    Input: {
      colorBgContainer: '#ffffff',
      colorBorder: 'rgba(0,0,0,0.10)',
      colorTextPlaceholder: '#c4b89e',
      activeBorderColor: '#19c8b9',
      hoverBorderColor: 'rgba(0,0,0,0.18)',
    },
    Select: {
      colorBgElevated: '#ffffff',
      optionSelectedBg: 'rgba(25,200,185,0.10)',
      optionActiveBg: 'rgba(25,200,185,0.05)',
    },
    Rate: {
      starColor: '#f5c31c',
      starSize: 18,
    },
  },
};

export function getTheme(mode: ThemeMode): ThemeConfig {
  return mode === 'light' ? lightTheme : cinemaNoirTheme;
}
