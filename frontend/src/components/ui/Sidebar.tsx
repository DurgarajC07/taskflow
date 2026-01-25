import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';
import {
  Home,
  Folder,
  CheckCircle,
  Users,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  Plus,
  LayoutGrid,
  Clock,
  Bell,
} from 'lucide-react';

interface SidebarProps {
  className?: string;
}

const Sidebar: React.FC<SidebarProps> = ({ className }) => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { name: 'Projects', href: '/projects', icon: Folder },
    { name: 'Tasks', href: '/tasks', icon: CheckCircle },
    { name: 'Board', href: '/board', icon: LayoutGrid },
    { name: 'Calendar', href: '/calendar', icon: Clock },
    { name: 'Team', href: '/team', icon: Users },
    { name: 'Reports', href: '/reports', icon: BarChart3 },
  ];

  const bottomNavigation = [
    { name: 'Notifications', href: '/notifications', icon: Bell, badge: 3 },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  const isActive = (href: string) => location.pathname === href;

  return (
    <div
      className={cn(
        'fixed left-0 top-0 h-screen bg-gray-900 text-white transition-all duration-300 ease-in-out z-20 flex flex-col',
        collapsed ? 'w-16' : 'w-64',
        className
      )}
    >
      {/* Logo */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-gray-800">
        {!collapsed && (
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center font-bold">
              T
            </div>
            <span className="font-bold text-lg">TaskFlow Pro</span>
          </Link>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 hover:bg-gray-800 rounded-md transition-colors ml-auto"
        >
          {collapsed ? (
            <ChevronRight className="w-5 h-5" />
          ) : (
            <ChevronLeft className="w-5 h-5" />
          )}
        </button>
      </div>

      {/* Create Button */}
      <div className="p-3">
        <button
          className={cn(
            'w-full bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-all duration-200 flex items-center justify-center gap-2',
            collapsed ? 'p-2' : 'py-2.5 px-4'
          )}
        >
          <Plus className="w-5 h-5" />
          {!collapsed && <span className="font-medium">Create Task</span>}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => (
          <Link
            key={item.name}
            to={item.href}
            className={cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group',
              isActive(item.href)
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-800 hover:text-white'
            )}
          >
            <item.icon
              className={cn(
                'w-5 h-5 flex-shrink-0',
                isActive(item.href)
                  ? 'text-white'
                  : 'text-gray-400 group-hover:text-white'
              )}
            />
            {!collapsed && <span className="font-medium">{item.name}</span>}
          </Link>
        ))}
      </nav>

      {/* Bottom Navigation */}
      <div className="px-2 py-4 border-t border-gray-800 space-y-1">
        {bottomNavigation.map((item) => (
          <Link
            key={item.name}
            to={item.href}
            className={cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group relative',
              isActive(item.href)
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-800 hover:text-white'
            )}
          >
            <item.icon
              className={cn(
                'w-5 h-5 flex-shrink-0',
                isActive(item.href)
                  ? 'text-white'
                  : 'text-gray-400 group-hover:text-white'
              )}
            />
            {!collapsed && <span className="font-medium">{item.name}</span>}
            {item.badge && !collapsed && (
              <span className="ml-auto bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {item.badge}
              </span>
            )}
            {item.badge && collapsed && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                {item.badge}
              </span>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
};

export { Sidebar };
