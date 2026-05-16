const BASE = '/api';

export interface Project {
	id: string;
	name: string;
	created_at: string;
	file_count: number;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
	const res = await fetch(`${BASE}${path}`, {
		headers: { 'Content-Type': 'application/json' },
		...options
	});
	if (!res.ok) {
		const detail = await res.text();
		throw new Error(`${res.status}: ${detail}`);
	}
	if (res.status === 204) return undefined as T;
	return res.json();
}

export function listProjects(): Promise<Project[]> {
	return request('/projects');
}

export function createProject(name: string): Promise<Project> {
	return request('/projects', {
		method: 'POST',
		body: JSON.stringify({ name })
	});
}

export function deleteProject(id: string): Promise<void> {
	return request(`/projects/${id}`, { method: 'DELETE' });
}
