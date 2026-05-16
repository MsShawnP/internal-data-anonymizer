<script lang="ts">
	import { page } from '$app/stores';
	import SearchBar from '$lib/components/SearchBar.svelte';

	let projectId = $derived($page.params.id);
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
	.search-section {
		margin-top: 32px;
	}
</style>
