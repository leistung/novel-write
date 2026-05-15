import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, Spin } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import AppLayout from './components/AppLayout';

const Home = lazy(() => import('./pages/Home'));
const Books = lazy(() => import('./pages/Books'));
const BookDetail = lazy(() => import('./pages/BookDetail'));
const ChapterReader = lazy(() => import('./pages/ChapterReader'));
const WorkflowPanel = lazy(() => import('./pages/WorkflowPanel'));
const CreateBook = lazy(() => import('./pages/CreateBook'));
const Help = lazy(() => import('./pages/Help'));
const Settings = lazy(() => import('./pages/Settings'));
const OutlineView = lazy(() => import('./pages/OutlineView'));

// Dify 风格主题 - 深色专业主题
const theme = {
  token: {
    colorPrimary: '#7c3aed', // 紫色主色调
    colorSuccess: '#10b981',
    colorWarning: '#f59e0b',
    colorError: '#ef4444',
    colorInfo: '#6366f1',
    borderRadius: 8,
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif',
    // 深色主题色彩
    colorBgBase: '#0f172a',
    colorTextBase: '#f1f5f9',
    colorBgContainer: '#1e293b',
    colorBorder: '#334155',
  },
  components: {
    Button: {
      borderRadius: 8,
      controlHeight: 40,
    },
    Card: {
      borderRadius: 12,
    },
    Modal: {
      borderRadius: 16,
    },
  },
};

const Loading = () => (
  <div
    style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)',
    }}
  >
    <div style={{ textAlign: 'center' }}>
      <Spin size="large" style={{ marginBottom: 16 }} />
      <div style={{ color: '#94a3b8', fontSize: 14 }}>加载中...</div>
    </div>
  </div>
);

function App() {
  return (
    <ConfigProvider locale={zhCN} theme={theme}>
      <Suspense fallback={<Loading />}>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Home />} />
            <Route path="/books" element={<Books />} />
            <Route path="/create" element={<CreateBook />} />
            <Route path="/book/:bookId" element={<BookDetail />} />
            <Route path="/book/:bookId/outline" element={<OutlineView />} />
            <Route path="/book/:bookId/chapter/:chapterNum" element={<ChapterReader />} />
            <Route path="/book/:bookId/workflow/:workflowId" element={<WorkflowPanel />} />
            <Route path="/help" element={<Help />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </ConfigProvider>
  );
}

export default App;
