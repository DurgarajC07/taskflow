import { useState } from 'react';
import { Plus, Search, Filter, LayoutGrid, List } from 'lucide-react';
import { MainLayout } from '@/components/layout';
import { Button, Input, Select, EmptyState } from '@/components/ui';
import { ProjectCard } from '@/components/features';

// Sample projects data
const sampleProjects = [
  {
    id: '1',
    name: 'Website Redesign',
    description: 'Complete overhaul of company website with modern design and improved UX',
    status: 'active' as const,
    progress: 65,
    members: [
      { id: '1', name: 'John Doe', avatar: '' },
      { id: '2', name: 'Jane Smith', avatar: '' },
      { id: '3', name: 'Bob Wilson', avatar: '' },
      { id: '4', name: 'Alice Johnson', avatar: '' },
    ],
    tasksTotal: 24,
    tasksCompleted: 16,
    dueDate: 'Apr 15, 2024',
  },
  {
    id: '2',
    name: 'Mobile App Development',
    description: 'iOS and Android app for customer engagement and sales',
    status: 'active' as const,
    progress: 42,
    members: [
      { id: '5', name: 'Charlie Brown', avatar: '' },
      { id: '6', name: 'Diana Prince', avatar: '' },
      { id: '7', name: 'Eve Adams', avatar: '' },
    ],
    tasksTotal: 48,
    tasksCompleted: 20,
    dueDate: 'May 30, 2024',
  },
  {
    id: '3',
    name: 'API Integration',
    description: 'Integration with third-party payment and analytics services',
    status: 'on-hold' as const,
    progress: 28,
    members: [
      { id: '8', name: 'Frank Miller', avatar: '' },
      { id: '9', name: 'Grace Lee', avatar: '' },
    ],
    tasksTotal: 15,
    tasksCompleted: 4,
    dueDate: 'Jun 10, 2024',
  },
  {
    id: '4',
    name: 'Database Migration',
    description: 'Migrate from MySQL to PostgreSQL with zero downtime',
    status: 'completed' as const,
    progress: 100,
    members: [
      { id: '10', name: 'Henry Clark', avatar: '' },
      { id: '11', name: 'Ivy Chen', avatar: '' },
      { id: '12', name: 'Jack Wong', avatar: '' },
    ],
    tasksTotal: 12,
    tasksCompleted: 12,
    dueDate: 'Mar 01, 2024',
  },
  {
    id: '5',
    name: 'Marketing Campaign Q2',
    description: 'Digital marketing campaign for product launch',
    status: 'active' as const,
    progress: 15,
    members: [
      { id: '13', name: 'Kate Wilson', avatar: '' },
      { id: '14', name: 'Leo Martinez', avatar: '' },
      { id: '15', name: 'Maya Patel', avatar: '' },
      { id: '16', name: 'Noah Kim', avatar: '' },
      { id: '17', name: 'Olivia Green', avatar: '' },
      { id: '18', name: 'Peter Parker', avatar: '' },
    ],
    tasksTotal: 32,
    tasksCompleted: 5,
    dueDate: 'Jun 30, 2024',
  },
  {
    id: '6',
    name: 'Security Audit',
    description: 'Comprehensive security assessment and vulnerability fixes',
    status: 'active' as const,
    progress: 78,
    members: [
      { id: '19', name: 'Quinn Taylor', avatar: '' },
      { id: '20', name: 'Rachel Green', avatar: '' },
    ],
    tasksTotal: 18,
    tasksCompleted: 14,
    dueDate: 'Apr 05, 2024',
  },
];

const ProjectsPage = () => {
  const [projects] = useState(sampleProjects);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredProjects = projects.filter((project) => {
    const matchesSearch = project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         project.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || project.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleProjectClick = (projectId: string) => {
    console.log('Navigate to project:', projectId);
    // TODO: Navigate to project detail page
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
            <p className="text-sm text-gray-500 mt-1">
              {filteredProjects.length} project{filteredProjects.length !== 1 ? 's' : ''}
            </p>
          </div>
          <Button variant="primary" leftIcon={<Plus className="w-4 h-4" />}>
            New Project
          </Button>
        </div>

        {/* Filters & Search */}
        <div className="flex items-center gap-4 bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex-1">
            <Input
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              leftIcon={<Search className="w-4 h-4" />}
            />
          </div>
          <Select
            options={[
              { label: 'All Status', value: 'all' },
              { label: 'Active', value: 'active' },
              { label: 'On Hold', value: 'on-hold' },
              { label: 'Completed', value: 'completed' },
            ]}
            value={statusFilter}
            onChange={(value) => setStatusFilter(value as string)}
            placeholder="Filter by status"
          />
          <Button variant="outline" leftIcon={<Filter className="w-4 h-4" />}>
            More Filters
          </Button>
          <div className="flex gap-1 border border-gray-300 rounded-lg p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${
                viewMode === 'grid' ? 'bg-gray-100' : 'hover:bg-gray-50'
              }`}
            >
              <LayoutGrid className="w-4 h-4 text-gray-600" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded ${
                viewMode === 'list' ? 'bg-gray-100' : 'hover:bg-gray-50'
              }`}
            >
              <List className="w-4 h-4 text-gray-600" />
            </button>
          </div>
        </div>

        {/* Projects Grid */}
        {filteredProjects.length > 0 ? (
          <div
            className={
              viewMode === 'grid'
                ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'
                : 'space-y-4'
            }
          >
            {filteredProjects.map((project) => (
              <ProjectCard
                key={project.id}
                {...project}
                onClick={() => handleProjectClick(project.id)}
              />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={Filter}
            title="No projects found"
            description="Try adjusting your search or filter criteria"
            actionLabel="Clear Filters"
            onAction={() => {
              setSearchQuery('');
              setStatusFilter('all');
            }}
          />
        )}
      </div>
    </MainLayout>
  );
};

export default ProjectsPage;
