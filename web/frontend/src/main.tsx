import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { cinemaNoirTheme } from './styles/theme';
import { AppProvider } from './context/AppContext';
import App from './App';
import './App.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider theme={cinemaNoirTheme} locale={zhCN}>
      <AppProvider>
        <App />
      </AppProvider>
    </ConfigProvider>
  </React.StrictMode>
);
