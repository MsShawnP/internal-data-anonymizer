<script lang="ts">
	interface LookupResult {
		column_name: string;
		original: string;
		anonymized: string;
		file_name: string | null;
	}

	interface Props {
		projectId: string;
	}

	let { projectId }: Props = $props();
	let query = $state('');
	let results = $state<LookupResult[]>([]);
	let loading = $state(false);
	let debounceTimer: ReturnType<typeof setTimeout> | null = null;

	function handleInput() {
		if (debounceTimer) clearTimeout(debounceTimer);
		if (!query.trim()) {
			results = [];
			return;
		}
		debounceTimer = setTimeout(search, 300);
	}

	async function search() {
		if (!query.trim()) return;
		loading = true;
		try {
			const res = await fetch(`/api/projects/${projectId}/reverse-lookup?q=${encodeURIComponent(query.trim())}`);
			if (res.ok) {
				results = await res.json();
			}
		} finally {
			loading = false;
		}
	}
</script>

<div class="search-bar">
	<input
		type="text"
		bind:value={query}
		oninput={handleInput}
		placeholder="Paste anonymized value to find original..."
	/>
	{#if loading}
		<span class="loading">Searching...</span>
	{/if}
</div>

{#if results.length > 0}
	<ul class="results">
		{#each results as r}
			<li class="result-item">
				<span class="anon-value">{r.anonymized}</span>
				<span class="arrow">→</span>
				<span class="orig-value">{r.original}</span>
				<span class="meta">{r.column_name}</span>
			</li>
		{/each}
	</ul>
{:else if query.trim() && !loading}
	<p class="no-results">No results found.</p>
{/if}

<style>
	.search-bar {
		position: relative;
		margin-bottom: 16px;
	}
	input {
		width: 100%;
		padding: 10px 14px;
		border: 1px solid #d8d4c8;
		border-radius: 2px;
		font-family: inherit;
		font-size: 15px;
		background: white;
		box-sizing: border-box;
	}
	input:focus {
		outline: 2px solid #2a2a2a;
		outline-offset: 2px;
	}
	.loading {
		position: absolute;
		right: 12px;
		top: 50%;
		transform: translateY(-50%);
		font-size: 12px;
		color: #6b6b6b;
	}
	.results {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	.result-item {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 10px 14px;
		border: 1px solid #e5e0d8;
		border-radius: 2px;
		margin-bottom: 6px;
		background: white;
		font-size: 14px;
	}
	.anon-value {
		font-weight: 600;
		color: #1b3a5c;
	}
	.arrow {
		color: #6b6b6b;
	}
	.orig-value {
		color: #2a2a2a;
	}
	.meta {
		margin-left: auto;
		font-size: 12px;
		color: #6b6b6b;
	}
	.no-results {
		font-size: 14px;
		color: #6b6b6b;
	}
</style>
