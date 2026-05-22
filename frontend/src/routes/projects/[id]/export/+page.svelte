<script lang="ts">
	import { page } from '$app/stores';

	let projectId = $derived($page.params.id);
	let fileId = $derived($page.url.searchParams.get('file_id'));

	let format = $state('csv');
	let exporting = $state(false);
	let error = $state('');
	let downloadUrl = $state<string | null>(null);

	const FORMATS = [
		{ value: 'csv', label: 'CSV (.csv)' },
		{ value: 'xlsx', label: 'Excel (.xlsx)' },
		{ value: 'json', label: 'JSON (.json)' },
		{ value: 'parquet', label: 'Parquet (.parquet)' }
	];

	async function handleExport() {
		if (!fileId) return;
		exporting = true;
		error = '';

		try {
			const res = await fetch(
				`/api/projects/${projectId}/files/${fileId}/export?format=${format}`
			);
			if (!res.ok) {
				const detail = await res.json().catch(() => ({ detail: `Export failed (${res.status})` }));
				error = detail.detail || `Export failed (${res.status})`;
				return;
			}
			const blob = await res.blob();
			downloadUrl = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = downloadUrl;
			a.download = `anonymized.${format}`;
			a.click();
		} catch (e) {
			error = 'Network error during export';
		} finally {
			exporting = false;
		}
	}
</script>

<div class="export-page">
	<header>
		<a href="/projects/{projectId}" class="back">← Back to Project</a>
		<h1>Export</h1>
		<p class="subtitle">Download your anonymized file in the format you need.</p>
	</header>

	{#if !fileId}
		<p class="status error">No file specified. Complete the review flow first.</p>
	{:else}
		<fieldset class="format-picker">
			<legend class="format-label">Output format</legend>
			<div class="format-options">
				{#each FORMATS as fmt}
					<label class="format-option" class:selected={format === fmt.value}>
						<input
							type="radio"
							name="format"
							value={fmt.value}
							bind:group={format}
						/>
						{fmt.label}
					</label>
				{/each}
			</div>
		</fieldset>

		<button class="export-btn" onclick={handleExport} disabled={exporting}>
			{exporting ? 'Exporting...' : 'Download'}
		</button>

		{#if error}
			<p class="status error">{error}</p>
		{/if}
	{/if}
</div>

<style>
	.export-page {
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
		font-size: 22px;
		font-weight: 700;
		margin: 8px 0 0;
	}
	.subtitle {
		font-size: 14px;
		color: var(--ll-london-35);
		margin: 4px 0 0;
	}
	.format-picker {
		margin-bottom: 24px;
		border: none;
		padding: 0;
	}
	.format-label {
		display: block;
		font-size: 14px;
		font-weight: 600;
		margin-bottom: 8px;
		padding: 0;
	}
	.format-options {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}
	.format-option {
		padding: 8px 16px;
		border: 1px solid var(--ll-london-85);
		border-radius: 2px;
		cursor: pointer;
		font-size: 14px;
		background: white;
	}
	.format-option:hover {
		border-color: var(--ll-chicago-20);
	}
	.format-option.selected {
		border-color: var(--ll-chicago-20);
		background: var(--ll-canvas);
		font-weight: 600;
	}
	.format-option input {
		display: none;
	}
	.export-btn {
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
	.export-btn:hover:not(:disabled) {
		background: var(--ll-chicago-10);
	}
	.export-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	.status.error {
		color: var(--ll-red-42);
		font-size: 14px;
		margin-top: 12px;
	}
</style>
