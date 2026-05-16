<script lang="ts">
	import { page } from '$app/stores';
	import SearchBar from '$lib/components/SearchBar.svelte';

	let projectId = $derived($page.params.id);
</script>

<div class="lookup-page">
	<header>
		<a href="/projects/{projectId}" class="back">← Back to Project</a>
		<h1>Reverse Lookup</h1>
		<p class="subtitle">Paste or type an anonymized value to find the original.</p>
	</header>

	<SearchBar {projectId} />
</div>

<style>
	.lookup-page {
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
	.subtitle {
		font-size: 14px;
		color: #6b6b6b;
		margin: 4px 0 0;
	}
</style>
