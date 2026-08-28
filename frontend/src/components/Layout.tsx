import { Outlet, Link, NavLink, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/auth'
import { getUnreadCount } from '@/lib/api'
import { useTheme } from '@/components/theme-provider'
import {
  LogOut,
  Settings,
  BookOpen,
  HelpCircle,
  CreditCard,
  MessageCircle,
  Shield,
  LayoutGrid,
  LogIn,
  UserPlus,
  Feather,
  Sun,
  Moon,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuGroup,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

const navCls = ({ isActive }: { isActive: boolean }) =>
  `px-2 py-1.5 text-sm rounded-lg flex items-center gap-1.5 transition ${
    isActive
      ? 'bg-primary/10 text-primary font-medium'
      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
  }`

export default function Layout() {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()
  const { theme, toggle } = useTheme()
  const isBusiness = user?.version === 'business'
  const isAdmin = user?.is_admin === true

  // 未读消息计数（仅登录后查询，用于导航 badge）
  const { data: unreadData } = useQuery({
    queryKey: ['unread-count'],
    queryFn: getUnreadCount,
    refetchInterval: 30 * 1000,
    retry: false,
    enabled: !!user,
  })
  const unread = unreadData?.unread ?? 0

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <div className="h-full flex flex-col">
      <header className="glass border-b sticky top-0 z-20">
        <div className="w-full max-w-[1600px] mx-auto px-4 md:px-8 h-14 flex items-center gap-3">
          <Link to="/" className="flex items-center gap-2 shrink-0 mr-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white">
              <Feather size={16} />
            </div>
            <span className="font-bold text-lg text-gray-900">StoryClaw</span>
          </Link>

          {user ? (
            <>
              <Badge variant={isBusiness ? 'default' : 'secondary'} className="hidden sm:inline-flex">
                {isBusiness ? '商业版' : '本地版'}
              </Badge>
              {isBusiness && (
                <Badge variant="outline" className="hidden sm:inline-flex bg-amber-50 text-amber-700 border-amber-200">
                  剩余积分 {user?.credits_balance ?? 0}
                </Badge>
              )}
            </>
          ) : (
            <Badge variant="secondary" className="hidden sm:inline-flex">
              未登录
            </Badge>
          )}

          <div className="ml-auto flex items-center gap-1">
            <button
              type="button"
              onClick={toggle}
              title={theme === 'dark' ? '切换到浅色模式' : '切换到深色模式'}
              className="ml-1 flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition hover:bg-muted hover:text-foreground"
            >
              {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
            </button>
            {user ? (
              <>
                <NavLink to="/" end className={navCls}>
                  <LayoutGrid size={16} /> 我的作品
                </NavLink>
                <NavLink to="/community" className={navCls}>
                  <BookOpen size={16} /> 社区
                </NavLink>
                <NavLink to="/help" className={navCls}>
                  <HelpCircle size={16} /> 帮助
                </NavLink>
                <NavLink to="/recharge" className={navCls}>
                  <CreditCard size={16} /> 充值
                </NavLink>
                <NavLink to="/messages" className={`${navCls} relative`}>
                  <MessageCircle size={16} /> 消息
                  {unread > 0 && (
                    <span className="absolute -top-1 -right-1 text-[10px] min-w-[16px] h-4 px-1 flex items-center justify-center rounded-full bg-red-500 text-white">
                      {unread > 99 ? '99+' : unread}
                    </span>
                  )}
                </NavLink>
                {isAdmin && (
                  <NavLink to="/admin" className={navCls}>
                    <Shield size={16} /> 后台
                  </NavLink>
                )}
                {!isBusiness && (
                  <NavLink to="/llm-configs" className={navCls}>
                    <Settings size={16} /> 配置
                  </NavLink>
                )}
                <DropdownMenu>
                  <DropdownMenuTrigger className="ml-1 flex items-center gap-2 rounded-lg p-1 hover:bg-muted transition outline-none">
                    <Avatar className="w-7 h-7">
                      <AvatarFallback className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white text-xs">
                        {user?.username?.slice(0, 1).toUpperCase() ?? 'U'}
                      </AvatarFallback>
                    </Avatar>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-52">
                    <DropdownMenuGroup>
                      <DropdownMenuLabel className="flex flex-col gap-0.5">
                        <span className="text-sm font-medium text-foreground">{user?.username}</span>
                        <span className="text-xs font-normal text-muted-foreground">
                          {isBusiness ? '商业版' : '本地版'}
                          {isBusiness ? ` · 积分 ${user?.credits_balance ?? 0}` : ''}
                        </span>
                      </DropdownMenuLabel>
                    </DropdownMenuGroup>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={handleLogout} className="text-destructive focus:text-destructive">
                      <LogOut size={16} /> 退出登录
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </>
            ) : (
              <>
                <NavLink to="/community" className={navCls}>
                  <BookOpen size={16} /> 社区
                </NavLink>
                <NavLink to="/help" className={navCls}>
                  <HelpCircle size={16} /> 帮助
                </NavLink>
                <NavLink to="/login">
                  <Button variant="outline" size="sm">
                    <LogIn size={15} /> 登录
                  </Button>
                </NavLink>
                <NavLink to="/register">
                  <Button size="sm">
                    <UserPlus size={15} /> 注册
                  </Button>
                </NavLink>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="flex-1 flex flex-col min-h-0">
        <div className="flex-1 flex flex-col min-h-0 w-full max-w-[1600px] mx-auto px-4 md:px-8 py-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
