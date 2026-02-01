import type { Project } from '../types';
import { spacing, colors } from '../../../lib/design-tokens';

interface ProjectListProps {
  projects: Project[];
  isLoading?: boolean;
  onProjectClick?: (project: Project) => void;
}

export const ProjectList = ({ projects, isLoading, onProjectClick }: ProjectListProps) => {
  if (isLoading) {
    return (
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
          gap: spacing[6],
        }}
      >
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            style={{
              height: '200px',
              backgroundColor: colors.neutral[100],
              borderRadius: '0.5rem',
              animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            }}
          />
        ))}
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div
        style={{
          textAlign: 'center',
          padding: spacing[12],
        }}
      >
        <p style={{ fontSize: '0.875rem', color: colors.neutral[500] }}>
          No projects found. Create your first project to get started.
        </p>
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
        gap: spacing[6],
      }}
    >
      {projects.map((project) => (
        <div
          key={project.id}
          onClick={() => onProjectClick?.(project)}
          style={{
            backgroundColor: 'white',
            borderRadius: '0.75rem',
            padding: spacing[6],
            border: `1px solid ${colors.neutral[200]}`,
            cursor: 'pointer',
            transition: 'all 150ms',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1)';
            e.currentTarget.style.transform = 'translateY(-2px)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.boxShadow = 'none';
            e.currentTarget.style.transform = 'translateY(0)';
          }}
        >
          <div style={{ marginBottom: spacing[4] }}>
            <h3
              style={{
                fontSize: '1.125rem',
                fontWeight: 600,
                color: colors.neutral[900],
                marginBottom: spacing[2],
              }}
            >
              {project.name}
            </h3>
            <span
              style={{
                fontSize: '0.75rem',
                color: colors.neutral[500],
                fontWeight: 500,
              }}
            >
              {project.key}
            </span>
          </div>

          {project.description && (
            <p
              style={{
                fontSize: '0.875rem',
                color: colors.neutral[600],
                lineHeight: 1.5,
                marginBottom: spacing[4],
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}
            >
              {project.description}
            </p>
          )}

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingTop: spacing[4],
              borderTop: `1px solid ${colors.neutral[100]}`,
            }}
          >
            <div style={{ fontSize: '0.75rem', color: colors.neutral[600] }}>
              <span>{project.taskCount} tasks</span>
              {' • '}
              <span>{project.memberCount} members</span>
            </div>
            <div
              style={{
                fontSize: '0.75rem',
                fontWeight: 500,
                padding: `${spacing[1]} ${spacing[2]}`,
                borderRadius: '0.25rem',
                backgroundColor: colors.brand[100],
                color: colors.brand[700],
              }}
            >
              {Math.round(project.progress)}%
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
