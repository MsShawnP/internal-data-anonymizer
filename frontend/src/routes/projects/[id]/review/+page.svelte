<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { listColumns, updateColumnStrategy, type ColumnProfile, type Strategy } from '$lib/api';
	import ColumnCard from '$lib/components/ColumnCard.svelte';

	let projectId = $derived($page.params.id);
	let fileId = $derived($page.url.searchParams.get('file'));

	let columns = $state<ColumnProfile[]>([]);
	let currentIndex = $state(0);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let confirmedStrategies = $state<Record<string, Strategy>>({});
	let allConfirmed = $derived(Object.keys(confirmedStrategies).length === columns.length && columns.length > 0);
	let saving = $state(false);

	onMount(async () => {
		if (!fileId) {
			error = 'No file specified. Navigate here from the upload step.';
			loading = false;
			return;
		}
		try {
			columns = await listColumns(projectId, fileId);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load columns';
		} finally {
			loading = false;
		}
	});

	async function handleConfirm(strategy: Strategy) {
		if (!fileId) return;
		const col = columns[currentIndex];
		saving = true;
		try {
			await updateColumnStrategy(projectId, fileId, col.name, strategy);
			confirmedStrategies = { ...confirmedStrategies, [col.name]: strategy };
			if (currentIndex < columns.length - 1) {
				currentIndex++;
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to save strategy';
		} finally {
			saving = false;
		}
	}

	function goToColumn(index: number) {
		currentIndex = index;
	}
</script>

<div class="review-page">
	<header>
		<h1>Review Columns</h1>
		<p class="subtitle">Confirm or override the suggested anonymization strategy for each column.</p>
	</header>

	{#if loading}
		<p class="status">Loading column profiles...</p>
	{:else if error}
		<p class="status error">{error}</p>
	{:else if columns.length === 0}
		<p class="status">No columns found for this file.</p>
	{:else if allConfirmed}
		<div class="complete-state">
			<h2>All columns confirmed</h2>
			<p>All {columns.length} columns have been reviewed and strategies assigned.</p>
			<div class="summary">
				{#each columns as col}
					<div class="summary-row">
						<span class="summary-name">{col.name}</span>
						<span class="summary-strategy">{confirmedStrategies[col.name]}</span>
					</div>
				{/each}
			</div>
			<button class="generate-btn" disabled>
				Generate Mappings (coming soon)
			</button>
		</div>
	{:else}
		<div class="progress">
			<span class="progress-text">Column {currentIndex + 1} of {columns.length}</span>
			<div class="progress-bar">
				<div
					class="progress-fill"
					style="width: {(Object.keys(confirmedStrategies).length / columns.length) * 100}%"
				></div>
			</div>
			<span class="progress-count">{Object.keys(confirmedStrategies).length} confirmed</span>
		</div>

		<div class="column-nav">
			{#each columns as col, i}
				<button
					class="nav-dot"
					class:active={i === currentIndex}
					class:confirmed={col.name in confirmedStrategies}
					onclick={() => goToColumn(i)}
					title={col.name}
				>
					{i + 1}
				</button>
			{/each}
		</div>

		<ColumnCard
			column={columns[currentIndex]}
			onconfirm={handleConfirm}
		/>

		{#if saving}
			<p class="status saving">Saving...</p>
		{/if}
	{/if}
</div>

<style>
	.review-page {
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
		font-size: 15px;
		color: #6b6b6b;
		margin: 4px 0 0;
	}
	.status {
		color: #6b6b6b;
		font-size: 15px;
	}
	.status.error {
		color: #c54b4b;
	}
	.status.saving {
		text-align: center;
		margin-top: 12px;
	}
	.progress {
		display: flex;
		align-items: center;
		gap: 12px;
		margin-bottom: 20px;
	}
	.progress-text {
		font-size: 14px;
		font-weight: 600;
		white-space: nowrap;
	}
	.progress-bar {
		flex: 1;
		height: 4px;
		background: #e5e0d8;
		border-radius: 2px;
		overflow: hidden;
	}
	.progress-fill {
		height: 100%;
		background: #1b3a5c;
		transition: width 200ms ease-out;
	}
	.progress-count {
		font-size: 13px;
		color: #6b6b6b;
		white-space: nowrap;
	}
	.column-nav {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin-bottom: 20px;
	}
	.nav-dot {
		width: 28px;
		height: 28px;
		border-radius: 2px;
		border: 1px solid #d8d4c8;
		background: white;
		font-size: 12px;
		font-weight: 600;
		cursor: pointer;
		color: #2a2a2a;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.nav-dot:hover {
		border-color: #1b3a5c;
	}
	.nav-dot.active {
		background: #1b3a5c;
		color: white;
		border-color: #1b3a5c;
	}
	.nav-dot.confirmed {
		background: #e8f0e8;
		border-color: #4a7ba7;
	}
	.nav-dot.active.confirmed {
		background: #1b3a5c;
		color: white;
	}
	.complete-state {
		text-align: center;
		padding: 24px;
	}
	.complete-state h2 {
		font-family: 'Playfair Display', Georgia, serif;
		font-size: 22px;
		margin: 0 0 8px;
	}
	.complete-state p {
		color: #6b6b6b;
		font-size: 15px;
		margin: 0 0 24px;
	}
	.summary {
		max-width: 400px;
		margin: 0 auto 24px;
		text-align: left;
	}
	.summary-row {
		display: flex;
		justify-content: space-between;
		padding: 8px 0;
		border-bottom: 1px solid #e5e0d8;
		font-size: 14px;
	}
	.summary-name {
		font-weight: 600;
	}
	.summary-strategy {
		color: #6b6b6b;
	}
	.generate-btn {
		padding: 10px 24px;
		background: #1b3a5c;
		color: white;
		border: none;
		border-radius: 2px;
		font-family: inherit;
		font-size: 15px;
		font-weight: 600;
		cursor: pointer;
	}
	.generate-btn:hover:not(:disabled) {
		background: #14304b;
	}
	.generate-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
</style>
