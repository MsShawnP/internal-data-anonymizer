<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import SearchBar from '$lib/components/SearchBar.svelte';

	interface FileRecord {
		id: string;
		filename: string;
		uploaded_at: string;
		row_count: number;
		column_count: number;
	}

	let projectId = $derived($page.params.id);
	let files = $state<FileRecord[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			const res = await fetch(`/api/projects/${projectId}/files`);
			if (res.ok) files = await res.json();
		} finally {
			loading = false;
		}
	});

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('en-US', {
			month: 'short', day: 'numeric', year: 'numeric'
		});
	}
</script>

<div class="project-view">
	<header>
		<a href="/" class="back">← Dashboard</a>
		<h1>Project</h1>
	</header>

	<nav class="actions">
		<a href="/projects/{projectId}/upload" class="btn">Upload File</a>
		<a href="/projects/{projectId}/lookup" class="btn-secondary">Reverse Lookup</a>
	</nav>

	{#if loading}
		<p class="status">Loading files...</p>
	{:else if files.length > 0}
		<section class="files-section">
			<h2>Files</h2>
			<ul class="file-list">
				{#each files as file (file.id)}
					<li class="file-card">
						<a href="/projects/{projectId}/review?file_id={file.id}" class="file-link">
							<span class="file-name">{file.filename}</span>
							<span class="file-meta">
								{formatDate(file.uploaded_at)} · {file.row_count} rows · {file.column_count} columns
							</span>
						</a>
					</li>
				{/each}
			</ul>
		</section>
	{/if}

	<section class="search-section">
		<h2>Quick Lookup</h2>
		<SearchBar {projectId} />
	</section>
</div>

<style>
	.project-view {
		max-width: 700px;
		margin: 0 auto;
		padding: 48px 24px;
	}
	header {
		margin-bottom: 24px;
	}
	.back {
		font-size: 13px;
		color: #6b6b6b;
		text-decoration: none;
	}
	.back:hover {
		color: #2a2a2a;
	}
	h1 {
		font-family: 'Playfair Display', Georgia, serif;
		font-size: 22px;
		font-weight: 700;
		margin: 8px 0 0;
	}
	h2 {
		font-size: 16px;
		font-weight: 600;
		margin: 0 0 12px;
	}
	.actions {
		display: flex;
		gap: 8px;
		margin-bottom: 32px;
	}
	.btn {
		padding: 8px 16px;
		background: #1b3a5c;
		color: white;
		border-radius: 2px;
		text-decoration: none;
		font-size: 14px;
		font-weight: 600;
	}
	.btn:hover {
		background: #14304b;
	}
	.btn-secondary {
		padding: 8px 16px;
		background: white;
		color: #1b3a5c;
		border: 1px solid #d8d4c8;
		border-radius: 2px;
		text-decoration: none;
		font-size: 14px;
		font-weight: 600;
	}
	.btn-secondary:hover {
		background: #f8f6f1;
	}
	.status {
		color: #6b6b6b;
		font-size: 15px;
	}
	.files-section {
		margin-bottom: 32px;
	}
	.file-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	.file-card {
		border: 1px solid #e5e0d8;
		border-radius: 2px;
		margin-bottom: 8px;
		background: white;
	}
	.file-link {
		display: flex;
		flex-direction: column;
		padding: 12px 16px;
		text-decoration: none;
		color: inherit;
	}
	.file-link:hover {
		background: #f8f6f1;
	}
	.file-name {
		font-weight: 600;
		font-size: 15px;
	}
	.file-meta {
		font-size: 13px;
		color: #6b6b6b;
		margin-top: 2px;
	}
	.search-section {
		margin-top: 32px;
	}
</style>
