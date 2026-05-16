import { listProjects, createProject, deleteProject, type Project } from '$lib/api';

class ProjectStore {
	projects = $state<Project[]>([]);
	loading = $state(false);
	error = $state<string | null>(null);

	async load() {
		this.loading = true;
		this.error = null;
		try {
			this.projects = await listProjects();
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Failed to load projects';
		} finally {
			this.loading = false;
		}
	}

	async create(name: string) {
		const project = await createProject(name);
		this.projects = [project, ...this.projects];
		return project;
	}

	async remove(id: string) {
		await deleteProject(id);
		this.projects = this.projects.filter((p) => p.id !== id);
	}
}

export const projectStore = new ProjectStore();
