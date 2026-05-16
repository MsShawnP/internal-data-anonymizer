<script lang="ts">
	interface Props {
		projectId: string;
		columns: string[];
		rows: Record<string, string>[];
	}

	let { projectId, columns, rows }: Props = $props();
	let revealedCell = $state<{ row: number; col: string } | null>(null);
	let originalValue = $state<string | null>(null);
	let loading = $state(false);

	async function handleCellClick(rowIdx: number, col: string, anonymizedValue: string) {
		if (revealedCell?.row === rowIdx && revealedCell?.col === col) {
			revealedCell = null;
			originalValue = null;
			return;
		}

		loading = true;
		revealedCell = { row: rowIdx, col };
		try {
			const res = await fetch(
				`/api/projects/${projectId}/reverse-lookup?q=${encodeURIComponent(anonymizedValue)}`
			);
			if (res.ok) {
				const results = await res.json();
				const match = results.find(
					(r: { anonymized: string }) => r.anonymized === anonymizedValue
				);
				originalValue = match?.original ?? 'Not found';
			}
		} finally {
			loading = false;
		}
	}
</script>

<div class="data-preview">
	<div class="table-scroll">
		<table>
			<thead>
				<tr>
					{#each columns as col}
						<th>{col}</th>
					{/each}
				</tr>
			</thead>
			<tbody>
				{#each rows as row, rowIdx}
					<tr>
						{#each columns as col}
							<td
								class="cell"
								class:revealed={revealedCell?.row === rowIdx && revealedCell?.col === col}
								onclick={() => handleCellClick(rowIdx, col, row[col])}
							>
								{#if revealedCell?.row === rowIdx && revealedCell?.col === col}
									<span class="original-badge">
										{loading ? '...' : originalValue}
									</span>
								{:else}
									{row[col] ?? ''}
								{/if}
							</td>
						{/each}
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
	<p class="hint">Click any cell to reveal its original value.</p>
</div>

<style>
	.data-preview {
		margin-top: 16px;
	}
	.table-scroll {
		overflow-x: auto;
		border: 1px solid #e5e0d8;
		border-radius: 2px;
		max-height: 500px;
		overflow-y: auto;
	}
	table {
		width: 100%;
		border-collapse: collapse;
		font-size: 13px;
		font-family: monospace;
	}
	th {
		position: sticky;
		top: 0;
		background: #f8f6f1;
		padding: 8px 10px;
		text-align: left;
		font-size: 12px;
		font-weight: 600;
		font-family: 'Source Sans 3', sans-serif;
		border-bottom: 1px solid #e5e0d8;
		white-space: nowrap;
	}
	td {
		padding: 5px 10px;
		border-bottom: 1px solid #f0ece5;
		white-space: nowrap;
		max-width: 200px;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.cell {
		cursor: pointer;
	}
	.cell:hover {
		background: #f0ece5;
	}
	.revealed {
		background: #1b3a5c !important;
		color: white;
	}
	.original-badge {
		font-weight: 600;
	}
	.hint {
		font-size: 12px;
		color: #6b6b6b;
		margin-top: 8px;
	}
</style>
