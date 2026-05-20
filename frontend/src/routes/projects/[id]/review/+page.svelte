<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { listColumns, updateColumnStrategy, type ColumnProfile, type Strategy } from '$lib/api';
	import ColumnCard from '$lib/components/ColumnCard.svelte';
	import MappingTable from '$lib/components/MappingTable.svelte';
	import PatternRuleEditor from '$lib/components/PatternRuleEditor.svelte';
	import Histogram from '$lib/components/Histogram.svelte';

	interface Mapping {
		original: string;
		anonymized: string;
	}

	let projectId = $derived($page.params.id);
	let fileId = $derived($page.url.searchParams.get('file_id') ?? $page.url.searchParams.get('file'));

	let columns = $state<ColumnProfile[]>([]);
	let currentIndex = $state(0);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let confirmedStrategies = $state<Record<string, Strategy>>({});
	let allConfirmed = $derived(Object.keys(confirmedStrategies).length === columns.length && columns.length > 0);
	let saving = $state(false);

	type Phase = 'strategy' | 'mappings' | 'done';
	let phase = $state<Phase>('strategy');
	let mappingIndex = $state(0);
	let columnMappings = $state<Record<string, Mapping[]>>({});
	let generating = $state(false);
	let approvedColumns = $state<Set<string>>(new Set());
	let allMappingsApproved = $derived(
		approvedColumns.size === columns.filter(c => confirmedStrategies[c.name] !== 'drop' && confirmedStrategies[c.name] !== 'passthrough').length
	);

	let jitterResults = $state<Record<string, { bin_edges: number[]; original_counts: number[]; jittered_counts: number[]; stats: { original_mean: number; original_std: number; jittered_mean: number; jittered_std: number } }>>({});

	let mappableColumns = $derived(
		columns.filter(c => {
			const s = confirmedStrategies[c.name];
			return s && s !== 'drop' && s !== 'passthrough';
		})
	);

	let currentMappingCol = $derived(mappableColumns[mappingIndex]);

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

	async function generateAllMappings() {
		if (!fileId) return;
		generating = true;
		error = null;

		for (const col of mappableColumns) {
			const strategy = confirmedStrategies[col.name];
			if (strategy === 'jitter') {
				try {
					const res = await fetch(`/api/projects/${projectId}/files/${fileId}/columns/${col.name}/jitter`, {
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify({ alpha: 0.05 })
					});
					if (res.ok) {
						jitterResults = { ...jitterResults, [col.name]: await res.json() };
					}
				} catch {}
				continue;
			}
			try {
				const res = await fetch(`/api/projects/${projectId}/files/${fileId}/columns/${col.name}/generate`, {
					method: 'POST'
				});
				if (res.ok) {
					const data = await res.json();
					columnMappings = { ...columnMappings, [col.name]: data.mappings };
				} else {
					error = `Failed to generate mappings for ${col.name}`;
					generating = false;
					return;
				}
			} catch (e) {
				error = `Network error generating mappings for ${col.name}`;
				generating = false;
				return;
			}
		}
		generating = false;
		phase = 'mappings';
		mappingIndex = 0;
	}

	async function handleMappingEdit(original: string, newValue: string) {
		if (!currentMappingCol) return;
		try {
			await fetch(`/api/projects/${projectId}/mappings/${currentMappingCol.name}/${encodeURIComponent(original)}`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ anonymized: newValue })
			});
			const updated = columnMappings[currentMappingCol.name].map(m =>
				m.original === original ? { ...m, anonymized: newValue } : m
			);
			columnMappings = { ...columnMappings, [currentMappingCol.name]: updated };
		} catch {}
	}

	async function handleRegenerate() {
		if (!fileId || !currentMappingCol) return;
		generating = true;
		try {
			const res = await fetch(`/api/projects/${projectId}/files/${fileId}/columns/${currentMappingCol.name}/generate`, {
				method: 'POST'
			});
			if (res.ok) {
				const data = await res.json();
				columnMappings = { ...columnMappings, [currentMappingCol.name]: data.mappings };
			}
		} finally {
			generating = false;
		}
	}

	function approveColumn() {
		if (!currentMappingCol) return;
		approvedColumns = new Set([...approvedColumns, currentMappingCol.name]);
		if (mappingIndex < mappableColumns.length - 1) {
			mappingIndex++;
		} else {
			phase = 'done';
		}
	}

	function goToMappingColumn(index: number) {
		mappingIndex = index;
	}

	async function handlePatternApply(pattern: string) {
		if (!fileId || !currentMappingCol) return;
		generating = true;
		try {
			const res = await fetch(`/api/projects/${projectId}/files/${fileId}/columns/${currentMappingCol.name}/generate`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ pattern })
			});
			if (res.ok) {
				const data = await res.json();
				columnMappings = { ...columnMappings, [currentMappingCol.name]: data.mappings };
			}
		} finally {
			generating = false;
		}
	}

	function handleExport() {
		goto(`/projects/${projectId}/export?file_id=${fileId}`);
	}
</script>

<div class="review-page">
	<header>
		<a href="/projects/{projectId}" class="back">← Back to Project</a>
		{#if phase === 'strategy'}
			<h1>Review Columns</h1>
			<p class="subtitle">Confirm or override the suggested anonymization strategy for each column.</p>
		{:else if phase === 'mappings'}
			<h1>Review Mappings</h1>
			<p class="subtitle">Review, edit, or regenerate proposed anonymized values for each column.</p>
		{:else}
			<h1>Ready to Export</h1>
			<p class="subtitle">All mappings approved. Export your anonymized file.</p>
		{/if}
	</header>

	{#if loading}
		<p class="status">Loading column profiles...</p>
	{:else if error}
		<p class="status error">{error}</p>
	{:else if columns.length === 0}
		<p class="status">No columns found for this file.</p>
	{:else if phase === 'strategy'}
		{#if allConfirmed}
			<div class="complete-state">
				<h2>All strategies confirmed</h2>
				<p>All {columns.length} columns have been reviewed.</p>
				<div class="summary">
					{#each columns as col}
						<div class="summary-row">
							<span class="summary-name">{col.name}</span>
							<span class="summary-strategy">{confirmedStrategies[col.name]}</span>
						</div>
					{/each}
				</div>
				<button class="generate-btn" onclick={generateAllMappings} disabled={generating}>
					{generating ? 'Generating...' : 'Generate Mappings'}
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
	{:else if phase === 'mappings'}
		<div class="progress">
			<span class="progress-text">Column {mappingIndex + 1} of {mappableColumns.length}</span>
			<div class="progress-bar">
				<div
					class="progress-fill"
					style="width: {(approvedColumns.size / mappableColumns.length) * 100}%"
				></div>
			</div>
			<span class="progress-count">{approvedColumns.size} approved</span>
		</div>

		<div class="column-nav">
			{#each mappableColumns as col, i}
				<button
					class="nav-dot"
					class:active={i === mappingIndex}
					class:confirmed={approvedColumns.has(col.name)}
					onclick={() => goToMappingColumn(i)}
					title={col.name}
				>
					{i + 1}
				</button>
			{/each}
		</div>

		{#if currentMappingCol}
			<div class="mapping-review-card">
				<div class="mapping-header">
					<h2>{currentMappingCol.name}</h2>
					<span class="strategy-badge">{confirmedStrategies[currentMappingCol.name]}</span>
				</div>

				{#if confirmedStrategies[currentMappingCol.name] === 'jitter'}
					{#if jitterResults[currentMappingCol.name]}
						{@const jr = jitterResults[currentMappingCol.name]}
						<Histogram
							binEdges={jr.bin_edges}
							originalCounts={jr.original_counts}
							jitteredCounts={jr.jittered_counts}
							stats={jr.stats}
						/>
					{:else}
						<p class="status">No jitter preview available.</p>
					{/if}
				{:else if columnMappings[currentMappingCol.name]}
					<MappingTable
						mappings={columnMappings[currentMappingCol.name]}
						onEdit={handleMappingEdit}
					/>

					<div class="mapping-actions">
						<button class="action-btn" onclick={handleRegenerate} disabled={generating}>
							{generating ? 'Regenerating...' : 'Regenerate All'}
						</button>
					</div>

					<PatternRuleEditor
						detectedType={currentMappingCol.detected_type}
						sampleValues={currentMappingCol.sample_values}
						onApply={handlePatternApply}
					/>
				{/if}

				<button class="approve-btn" onclick={approveColumn}>
					Approve & Next
				</button>
			</div>
		{/if}
	{:else}
		<div class="complete-state">
			<h2>All mappings approved</h2>
			<p>Your anonymization rules are ready. Export the file with mappings applied.</p>
			<button class="generate-btn" onclick={handleExport}>
				Export Anonymized File
			</button>
		</div>
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
	.back {
		font-size: 13px;
		color: var(--ll-london-35);
		text-decoration: none;
	}
	.back:hover {
		color: var(--ll-london-20);
	}
	h1 {
		font-family: 'Playfair Display', Georgia, serif;
		font-size: 26px;
		font-weight: 700;
		margin: 8px 0 0;
		letter-spacing: -0.01em;
	}
	.subtitle {
		font-size: 15px;
		color: var(--ll-london-35);
		margin: 4px 0 0;
	}
	.status {
		color: var(--ll-london-35);
		font-size: 15px;
	}
	.status.error {
		color: var(--ll-red-42);
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
		background: var(--ll-london-85);
		border-radius: 2px;
		overflow: hidden;
	}
	.progress-fill {
		height: 100%;
		background: var(--ll-chicago-20);
		transition: width 200ms ease-out;
	}
	.progress-count {
		font-size: 13px;
		color: var(--ll-london-35);
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
		border: 1px solid var(--ll-london-85);
		background: white;
		font-size: 12px;
		font-weight: 600;
		cursor: pointer;
		color: var(--ll-london-20);
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.nav-dot:hover {
		border-color: var(--ll-chicago-20);
	}
	.nav-dot.active {
		background: var(--ll-chicago-20);
		color: white;
		border-color: var(--ll-chicago-20);
	}
	.nav-dot.confirmed {
		background: var(--ll-hk-95);
		border-color: var(--ll-hk-35);
	}
	.nav-dot.active.confirmed {
		background: var(--ll-chicago-20);
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
		color: var(--ll-london-35);
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
		border-bottom: 1px solid var(--ll-london-85);
		font-size: 14px;
	}
	.summary-name {
		font-weight: 600;
	}
	.summary-strategy {
		color: var(--ll-london-35);
	}
	.generate-btn {
		padding: 10px 24px;
		background: var(--ll-chicago-20);
		color: white;
		border: none;
		border-radius: 2px;
		font-family: inherit;
		font-size: 15px;
		font-weight: 600;
		cursor: pointer;
	}
	.generate-btn:hover:not(:disabled) {
		background: var(--ll-chicago-10);
	}
	.generate-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	.mapping-review-card {
		border: 1px solid var(--ll-london-85);
		border-radius: 2px;
		padding: 20px;
		background: white;
	}
	.mapping-header {
		display: flex;
		align-items: center;
		gap: 12px;
		margin-bottom: 16px;
	}
	.mapping-header h2 {
		font-size: 16px;
		font-weight: 600;
		margin: 0;
	}
	.strategy-badge {
		font-size: 12px;
		padding: 2px 8px;
		background: var(--ll-canvas);
		border: 1px solid var(--ll-london-85);
		border-radius: 2px;
		color: var(--ll-london-35);
	}
	.mapping-actions {
		display: flex;
		gap: 8px;
		margin-top: 12px;
	}
	.action-btn {
		padding: 6px 12px;
		border: 1px solid var(--ll-london-85);
		border-radius: 2px;
		background: white;
		cursor: pointer;
		font-size: 13px;
		font-weight: 600;
	}
	.action-btn:hover:not(:disabled) {
		border-color: var(--ll-chicago-20);
		color: var(--ll-chicago-20);
	}
	.action-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	.approve-btn {
		width: 100%;
		margin-top: 16px;
		padding: 10px 20px;
		background: var(--ll-chicago-20);
		color: white;
		border: none;
		border-radius: 2px;
		font-family: inherit;
		font-size: 15px;
		font-weight: 600;
		cursor: pointer;
	}
	.approve-btn:hover {
		background: var(--ll-chicago-10);
	}
</style>
