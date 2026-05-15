import { useState, useMemo } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  HomeOutlined,
  BookOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SettingOutlined,
  QuestionCircleOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { Tooltip, Badge } from 'antd';

interface MenuItem {
  key: string;
  label: string;
  icon: React.ReactNode;
  badge?: number;
}

const menuItems: MenuItem[] = [
  { key: '/', label: '工作台', icon: <HomeOutlined /> },
  { key: '/books', label: '我的书籍', icon: <BookOutlined />, badge: 3 },
];

const bottomMenuItems: MenuItem[] = [
  { key: '/help', label: '帮助中心', icon: <QuestionCircleOutlined /> },
  { key: '/settings', label: '设置', icon: <SettingOutlined /> },
];

const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const selectedKey = useMemo(() => {
    if (location.pathname === '/') return '/';
    if (location.pathname.startsWith('/books')) return '/books';
    if (location.pathname.startsWith('/create')) return '/create';
    if (location.pathname.startsWith('/book/')) return '/books';
    if (location.pathname.startsWith('/help')) return '/help';
    if (location.pathname.startsWith('/settings')) return '/settings';
    return '/';
  }, [location.pathname]);

  const pageTitle = useMemo(() => {
    if (location.pathname === '/') return { title: '工作台', desc: '管理和创作你的小说项目' };
    if (location.pathname === '/books') return { title: '我的书籍', desc: '查看和管理你的所有书籍' };
    if (location.pathname === '/create') return { title: '创建新书', desc: '填写信息创建新的小说项目' };
    if (location.pathname.startsWith('/book/')) return { title: '书籍详情', desc: '查看和管理书籍内容' };
    if (location.pathname === '/help') return { title: '帮助中心', desc: '查看使用文档和常见问题' };
    if (location.pathname === '/settings') return { title: '设置', desc: '配置应用偏好' };
    return { title: '工作台', desc: '管理和创作你的小说项目' };
  }, [location.pathname]);

  const sidebarWidth = collapsed ? 72 : 260;

  // Dify 风格配色
  const colors = {
    bg: '#0f172a',
    sidebar: '#1e293b',
    sidebarHover: '#334155',
    primary: '#7c3aed',
    primaryLight: '#8b5cf6',
    text: '#f1f5f9',
    textSecondary: '#94a3b8',
    border: '#334155',
  };

  const renderMenuItem = (item: MenuItem, isBottom = false) => {
    const isSelected = selectedKey === item.key;

    const menuItemContent = (
      <div
        key={item.key}
        onClick={() => navigate(item.key)}
        style={{
          height: 44,
          display: 'flex',
          alignItems: 'center',
          padding: collapsed ? '0' : '0 16px',
          margin: '0 12px',
          justifyContent: collapsed ? 'center' : 'flex-start',
          cursor: 'pointer',
          position: 'relative',
          color: isSelected ? colors.text : colors.textSecondary,
          background: isSelected
            ? `linear-gradient(135deg, ${colors.primary}20, ${colors.primaryLight}20)`
            : 'transparent',
          borderRadius: 10,
          transition: 'all 0.2s ease',
          gap: 12,
          userSelect: 'none',
          border: isSelected ? `1px solid ${colors.primary}40` : '1px solid transparent',
        }}
        onMouseEnter={(e) => {
          if (!isSelected) {
            e.currentTarget.style.background = colors.sidebarHover;
            e.currentTarget.style.color = colors.text;
          }
        }}
        onMouseLeave={(e) => {
          if (!isSelected) {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = colors.textSecondary;
          }
        }}
      >
        <span
          style={{
            fontSize: 18,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 24,
            flexShrink: 0,
            color: isSelected ? colors.primaryLight : 'inherit',
          }}
        >
          {item.icon}
        </span>
        {!collapsed && (
          <span
            style={{
              fontSize: 14,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              fontWeight: isSelected ? 500 : 400,
              flex: 1,
            }}
          >
            {item.label}
          </span>
        )}
        {!collapsed && item.badge && item.badge > 0 && (
          <Badge
            count={item.badge}
            style={{
              backgroundColor: colors.primary,
              fontSize: 11,
              minWidth: 18,
              height: 18,
              lineHeight: '18px',
            }}
          />
        )}
      </div>
    );

    if (collapsed) {
      return (
        <Tooltip
          key={item.key}
          title={item.label}
          placement="right"
          overlayStyle={{ minWidth: 80 }}
          color={colors.sidebar}
        >
          {menuItemContent}
        </Tooltip>
      );
    }

    return menuItemContent;
  };

  return (
    <div
      style={{
        display: 'flex',
        minHeight: '100vh',
        background: colors.bg,
      }}
    >
      {/* Sidebar */}
      <aside
        style={{
          width: sidebarWidth,
          minWidth: sidebarWidth,
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          background: colors.sidebar,
          display: 'flex',
          flexDirection: 'column',
          transition: 'width 0.3s cubic-bezier(0.2, 0, 0, 1)',
          zIndex: 100,
          overflow: 'hidden',
          borderRight: `1px solid ${colors.border}`,
        }}
      >
        {/* Logo Area */}
        <div
          style={{
            height: 70,
            display: 'flex',
            alignItems: 'center',
            padding: collapsed ? '0' : '0 20px',
            borderBottom: `1px solid ${colors.border}`,
            flexShrink: 0,
            justifyContent: collapsed ? 'center' : 'flex-start',
            gap: 12,
          }}
        >
          {/* Gradient Logo Icon */}
          <div
            style={{
              width: 36,
              height: 36,
              minWidth: 36,
              borderRadius: 10,
              background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontSize: 16,
              fontWeight: 700,
              flexShrink: 0,
              boxShadow: `0 4px 14px ${colors.primary}40`,
            }}
          >
            N
          </div>
          {!collapsed && (
            <span
              style={{
                color: colors.text,
                fontSize: 18,
                fontWeight: 600,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                opacity: 1,
                transition: 'opacity 0.15s',
              }}
            >
              NovelWrite
            </span>
          )}
        </div>

        {/* New Book Button */}
        {!collapsed && (
          <div style={{ padding: '16px 20px' }}>
            <button
              onClick={() => navigate('/create')}
              style={{
                width: '100%',
                height: 44,
                borderRadius: 10,
                border: 'none',
                background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
                color: '#fff',
                fontSize: 14,
                fontWeight: 500,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                transition: 'all 0.2s ease',
                boxShadow: `0 4px 14px ${colors.primary}40`,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-1px)';
                e.currentTarget.style.boxShadow = `0 6px 20px ${colors.primary}60`;
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = `0 4px 14px ${colors.primary}40`;
              }}
            >
              <PlusOutlined />
              创建新书
            </button>
          </div>
        )}

        {collapsed && (
          <div style={{ padding: '16px 0', display: 'flex', justifyContent: 'center' }}>
            <Tooltip title="创建新书" placement="right" color={colors.sidebar}>
              <button
                onClick={() => navigate('/create')}
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 10,
                  border: 'none',
                  background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
                  color: '#fff',
                  fontSize: 18,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: `0 4px 14px ${colors.primary}40`,
                }}
              >
                <PlusOutlined />
              </button>
            </Tooltip>
          </div>
        )}

        {/* Navigation Menu */}
        <nav
          style={{
            flex: 1,
            padding: '8px 0',
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
            overflowY: 'auto',
          }}
        >
          <div style={{ padding: '0 8px 8px', color: colors.textSecondary, fontSize: 12 }}>
            {!collapsed && '主菜单'}
          </div>
          {menuItems.map((item) => renderMenuItem(item))}
        </nav>

        {/* Bottom Menu */}
        <div
          style={{
            borderTop: `1px solid ${colors.border}`,
            padding: '8px 0',
          }}
        >
          {bottomMenuItems.map((item) => renderMenuItem(item, true))}
        </div>

        {/* Collapse Button */}
        <div
          style={{
            padding: '12px 0',
            display: 'flex',
            justifyContent: 'center',
            borderTop: `1px solid ${colors.border}`,
          }}
        >
          <div
            onClick={() => setCollapsed(!collapsed)}
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: colors.sidebarHover,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              color: colors.textSecondary,
              fontSize: 14,
              transition: 'all 0.15s ease',
              userSelect: 'none',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = colors.primary;
              e.currentTarget.style.color = '#fff';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = colors.sidebarHover;
              e.currentTarget.style.color = colors.textSecondary;
            }}
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div
        style={{
          flex: 1,
          marginLeft: sidebarWidth,
          transition: 'margin-left 0.3s cubic-bezier(0.2, 0, 0, 1)',
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
          background: colors.bg,
        }}
      >
        {/* Header */}
        <header
          style={{
            height: 70,
            minHeight: 70,
            background: colors.sidebar,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 32px',
            borderBottom: `1px solid ${colors.border}`,
            position: 'sticky',
            top: 0,
            zIndex: 50,
          }}
        >
          {/* Page Title */}
          <div>
            <h1
              style={{
                margin: 0,
                fontSize: 20,
                fontWeight: 600,
                color: colors.text,
              }}
            >
              {pageTitle.title}
            </h1>
            <p
              style={{
                margin: '4px 0 0',
                fontSize: 13,
                color: colors.textSecondary,
              }}
            >
              {pageTitle.desc}
            </p>
          </div>

          {/* Right Side Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {/* User Avatar */}
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 10,
                background: `linear-gradient(135deg, ${colors.primary}, ${colors.primaryLight})`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontSize: 14,
                fontWeight: 600,
                cursor: 'pointer',
                flexShrink: 0,
                userSelect: 'none',
                boxShadow: `0 2px 8px ${colors.primary}40`,
              }}
            >
              U
            </div>
          </div>
        </header>

        {/* Content */}
        <main
          style={{
            flex: 1,
            padding: 32,
          }}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
