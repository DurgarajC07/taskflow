import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  Bell,
  HelpCircle,
  Settings,
  ChevronDown,
} from 'lucide-react';
import { Avatar } from './avatar';
import { useAuthStore } from '@/store/authStore';

interface HeaderProps {
  sidebarCollapsed?: boolean;
}

const Header: React.FC<HeaderProps> = ({ sidebarCollapsed = false }) => {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const { user, logout } = useAuthStore();

  return (
    <header
      className={`fixed top-0 right-0 h-16 bg-white border-b border-gray-200 z-10 transition-all duration-300 ${
        sidebarCollapsed ? 'left-16' : 'left-64'
      }`}
    >
      <div className="h-full px-4 flex items-center justify-between">
        {/* Left Section - Search */}
        <div className="flex items-center gap-4 flex-1">
          <div className="relative max-w-md w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search tasks, projects, people..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-2">
          {/* Quick Actions */}
          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <HelpCircle className="w-5 h-5 text-gray-600" />
          </button>

          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors relative">
            <Bell className="w-5 h-5 text-gray-600" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          <Link
            to="/settings"
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Settings className="w-5 h-5 text-gray-600" />
          </Link>

          {/* Divider */}
          <div className="w-px h-6 bg-gray-300 mx-2"></div>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-3 p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <Avatar
                src={user?.avatar ?? undefined}
                name={user?.email || 'User'}
                size="sm"
                status="online"
              />
              <div className="hidden md:block text-left">
                <p className="text-sm font-medium text-gray-900">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-xs text-gray-500 truncate max-w-[120px]">
                  {user?.email}
                </p>
              </div>
              <ChevronDown className="w-4 h-4 text-gray-500" />
            </button>

            {/* Dropdown Menu */}
            {showUserMenu && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowUserMenu(false)}
                ></div>
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-20">
                  <div className="px-4 py-3 border-b border-gray-200">
                    <p className="text-sm font-medium text-gray-900">
                      {user?.first_name} {user?.last_name}
                    </p>
                    <p className="text-xs text-gray-500">{user?.email}</p>
                  </div>
                  <div className="py-1">
                    <Link
                      to="/profile"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Your Profile
                    </Link>
                    <Link
                      to="/settings"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Settings
                    </Link>
                    <Link
                      to="/preferences"
                      className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      Preferences
                    </Link>
                  </div>
                  <div className="border-t border-gray-200 py-1">
                    <button
                      onClick={logout}
                      className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                    >
                      Sign out
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export { Header };
