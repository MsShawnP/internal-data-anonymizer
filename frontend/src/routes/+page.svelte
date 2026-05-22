<script lang="ts">
	import { onMount } from 'svelte';
	import { projectStore } from '$lib/stores/projects.svelte';
	import { formatDate } from '$lib/utils';

	let newName = $state('');
	let creating = $state(false);

	onMount(() => {
		projectStore.load();
	});

	async function handleCreate() {
		if (!newName.trim()) return;
		creating = true;
		try {
			await projectStore.create(newName.trim());
			newName = '';
		} finally {
			creating = false;
		}
	}

	async function handleDelete(id: string, name: string) {
		if (!confirm(`Delete project "${name}"? This cannot be undone.`)) return;
		await projectStore.remove(id);
	}
</script>

<div class="dashboard">
	<header>
		<h1>Data Anonymizer</h1>
		<p class="subtitle">Project Dashboard</p>
	</header>

	<form class="create-form" onsubmit={(e) => { e.preventDefault(); handleCreate(); }}>
		<input
			type="text"
			bind:value={newName}
			placeholder="New project name..."
			disabled={creating}
		/>
		<button type="submit" disabled={creating || !newName.trim()}>
			{creating ? 'Creating...' : 'Create Project'}
		</button>
	</form>

	{#if projectStore.loading}
		<p class="status">Loading projects...</p>
	{:else if projectStore.error}
		<p class="status error">{projectStore.error}</p>
	{:else if projectStore.projects.length === 0}
		<p class="status">No projects yet. Create one above.</p>
	{:else}
		<ul class="project-list">
			{#each projectStore.projects as project (project.id)}
				<li class="project-card">
					<a href="/projects/{project.id}" class="project-link">
						<span class="project-name">{project.name}</span>
						<span class="project-meta">
							{formatDate(project.created_at)} · {project.file_count} file{project.file_count !== 1 ? 's' : ''}
						</span>
					</a>
					<button
						class="delete-btn"
						onclick={() => handleDelete(project.id, project.name)}
						title="Delete project"
					>×</button>
				</li>
			{/each}
		</ul>
	{/if}
</div>

<style>
	.dashboard {
		max-width: 700px;
		margin: 0 auto;
		padding: 48px 24px;
	}
	header {
		margin-bottom: 32px;
	}
	h1 {
		font-family: 'Playfair Display', Georgia, serif;
		font-size: 26px;
		font-weight: 700;
		margin: 0;
		letter-spacing: -0.01em;
	}
	.subtitle {
		font-size: 14px;
		color: var(--ll-london-35);
		margin: 4px 0 0;
	}
	.create-form {
		display: flex;
		gap: 8px;
		margin-bottom: 24px;
	}
	input {
		flex: 1;
		padding: 8px 12px;
		border: 1px solid var(--ll-london-85);
		border-radius: 2px;
		font-family: inherit;
		font-size: 15px;
		background: white;
	}
	input:focus {
		outline: 2px solid var(--ll-london-20);
		outline-offset: 2px;
	}
	button {
		padding: 8px 16px;
		background: var(--ll-chicago-20);
		color: white;
		border: none;
		border-radius: 2px;
		font-family: inherit;
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
	}
	button:hover:not(:disabled) {
		background: var(--ll-chicago-10);
	}
	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	.status {
		color: var(--ll-london-35);
		font-size: 15px;
	}
	.status.error {
		color: var(--ll-red-42);
	}
	.project-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	.project-card {
		display: flex;
		align-items: center;
		border: 1px solid var(--ll-london-85);
		border-radius: 2px;
		margin-bottom: 8px;
		background: white;
	}
	.project-link {
		flex: 1;
		display: flex;
		flex-direction: column;
		padding: 12px 16px;
		text-decoration: none;
		color: inherit;
	}
	.project-link:hover {
		background: var(--ll-canvas);
	}
	.project-name {
		font-weight: 600;
		font-size: 15px;
	}
	.project-meta {
		font-size: 13px;
		color: var(--ll-london-35);
		margin-top: 2px;
	}
	.delete-btn {
		padding: 8px 12px;
		background: transparent;
		color: var(--ll-london-35);
		font-size: 18px;
		border: none;
		cursor: pointer;
	}
	.delete-btn:hover {
		color: var(--ll-red-42);
		background: transparent;
	}
</style>
