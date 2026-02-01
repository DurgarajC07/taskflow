import type { Project } from '../types';

interface ProjectCardProps {
  project: Project;
  onClick?: (project: Project) => void;
}

export const ProjectCard = ({ project, onClick }: ProjectCardProps) => {
  return (
    <div onClick={() => onClick?.(project)}>
      <h3>{project.name}</h3>
      <p>{project.description}</p>
    </div>
  );
};
