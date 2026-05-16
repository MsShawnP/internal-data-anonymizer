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

export interface ColumnProfile {
	name: string;
	dtype: string;
	strategy: string;
	detected_type: string;
	unique_count: number;
	null_rate: number;
	sample_values: string[];
	stats: Record<string, number>;
}

export type Strategy = 'fake' | 'jitter' | 'format-preserve' | 'hash' | 'drop' | 'passthrough';

export const STRATEGIES: Strategy[] = [
	'fake',
	'jitter',
	'format-preserve',
	'hash',
	'drop',
	'passthrough'
];

export function listColumns(projectId: string, fileId: string): Promise<ColumnProfile[]> {
	return request(`/projects/${projectId}/files/${fileId}/columns`);
}

export function updateColumnStrategy(
	projectId: string,
	fileId: string,
	colName: string,
	strategy: Strategy
): Promise<{ status: string; column: string; strategy: string }> {
	return request(`/projects/${projectId}/files/${fileId}/columns/${colName}/strategy`, {
		method: 'PUT',
		body: JSON.stringify({ strategy })
	});
}
