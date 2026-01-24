import { useAuth } from '../../hooks/useAuth';
import { LogOut } from 'lucide-react';

const DashboardPage = () => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <h1 className="text-2xl font-bold text-primary-600">TaskFlow Pro</h1>
            <div className="flex items-center space-x-4">
              <span className="text-gray-700">
                {user?.full_name || user?.email}
              </span>
              <button
                onClick={() => logout()}
                className="btn btn-secondary flex items-center space-x-2"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card">
          <h2 className="text-2xl font-bold mb-4">Welcome to TaskFlow Pro!</h2>
          <p className="text-gray-600">
            You're successfully authenticated. This is your dashboard.
          </p>
          <div className="mt-6 bg-primary-50 border border-primary-200 rounded-lg p-4">
            <h3 className="font-semibold text-primary-900 mb-2">User Information:</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex">
                <dt className="font-medium text-primary-700 w-32">Email:</dt>
                <dd className="text-primary-900">{user?.email}</dd>
              </div>
              <div className="flex">
                <dt className="font-medium text-primary-700 w-32">Name:</dt>
                <dd className="text-primary-900">{user?.full_name}</dd>
              </div>
              <div className="flex">
                <dt className="font-medium text-primary-700 w-32">Verified:</dt>
                <dd className="text-primary-900">{user?.is_verified ? 'Yes' : 'No'}</dd>
              </div>
              <div className="flex">
                <dt className="font-medium text-primary-700 w-32">Joined:</dt>
                <dd className="text-primary-900">
                  {user?.date_joined ? new Date(user.date_joined).toLocaleDateString() : 'N/A'}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </main>
    </div>
  );
};

export default DashboardPage;