import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider, App as AntdApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { getTheme } from './styles/theme';
import { useStore } from './store';
import App from './App';
import './App.css';

function ThemeBridge({ children }: { children: React.ReactNode }) {
  const theme = useStore((s) => s.theme);
  return (
    <ConfigProvider theme={getTheme(theme)} locale={zhCN}>
      {children}
    </ConfigProvider>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeBridge>
      <AntdApp>
        <App />
      </AntdApp>
    </ThemeBridge>
  </React.StrictMode>
);
