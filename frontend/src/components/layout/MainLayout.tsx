import { useState } from 'react';
import Sidebar from '@/components/ui/Sidebar';
import Header from '@/components/ui/Header';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [sidebarCollapsed, _setSidebarCollapsed] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar className={sidebarCollapsed ? 'w-16' : 'w-64'} />
      <Header sidebarCollapsed={sidebarCollapsed} />
      
      <main
        className={`pt-16 transition-all duration-300 ${
          sidebarCollapsed ? 'ml-16' : 'ml-64'
        }`}
      >
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  );
};

export default MainLayout;
