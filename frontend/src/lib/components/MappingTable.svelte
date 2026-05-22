<script lang="ts">
	interface Mapping {
		original: string;
		anonymized: string;
	}

	interface Props {
		mappings: Mapping[];
		onEdit: (original: string, newValue: string) => void;
	}

	let { mappings, onEdit }: Props = $props();
	let editingRow = $state<string | null>(null);
	let editValue = $state('');

	function startEdit(original: string, current: string) {
		editingRow = original;
		editValue = current;
	}

	function saveEdit(original: string) {
		if (editValue.trim()) {
			onEdit(original, editValue.trim());
		}
		editingRow = null;
	}

	function cancelEdit() {
		editingRow = null;
	}
</script>

<div class="mapping-table">
	<div class="table-header">
		<span class="col-original">Original</span>
		<span class="col-arrow"></span>
		<span class="col-anonymized">Anonymized</span>
	</div>
	<div class="table-body">
		{#each mappings as mapping (mapping.original)}
			<div class="table-row">
				<span class="col-original">{mapping.original}</span>
				<span class="col-arrow">→</span>
				{#if editingRow === mapping.original}
					<span class="col-anonymized editing">
						<input
							type="text"
							bind:value={editValue}
							onkeydown={(e) => {
								if (e.key === 'Enter') saveEdit(mapping.original);
								if (e.key === 'Escape') cancelEdit();
							}}
						/>
						<button class="save-btn" onclick={() => saveEdit(mapping.original)}>✓</button>
						<button class="cancel-btn" onclick={cancelEdit}>✕</button>
					</span>
				{:else}
					<button
						type="button"
						class="col-anonymized clickable"
						onclick={() => startEdit(mapping.original, mapping.anonymized)}
						title="Click to edit"
					>
						{mapping.anonymized}
					</button>
				{/if}
			</div>
		{/each}
	</div>
</div>

<style>
	.mapping-table {
		border: 1px solid var(--ll-london-85);
		border-radius: 2px;
		background: white;
		max-height: 400px;
		overflow-y: auto;
	}
	.table-header {
		display: grid;
		grid-template-columns: 1fr 30px 1fr;
		padding: 8px 12px;
		border-bottom: 1px solid var(--ll-london-85);
		font-size: 12px;
		font-weight: 600;
		color: var(--ll-london-35);
		text-transform: uppercase;
		letter-spacing: 0.04em;
		position: sticky;
		top: 0;
		background: var(--ll-canvas);
	}
	.table-body {
		font-size: 14px;
	}
	.table-row {
		display: grid;
		grid-template-columns: 1fr 30px 1fr;
		padding: 6px 12px;
		border-bottom: 1px solid var(--ll-london-90);
		align-items: center;
	}
	.table-row:last-child {
		border-bottom: none;
	}
	.col-arrow {
		text-align: center;
		color: var(--ll-london-35);
	}
	.col-original {
		font-family: monospace;
		font-size: 13px;
	}
	.col-anonymized {
		font-family: monospace;
		font-size: 13px;
	}
	.clickable {
		cursor: pointer;
		padding: 2px 4px;
		border-radius: 2px;
		border: none;
		background: none;
		font: inherit;
		text-align: left;
	}
	.clickable:hover {
		background: var(--ll-london-90);
	}
	.editing {
		display: flex;
		gap: 4px;
		align-items: center;
	}
	.editing input {
		flex: 1;
		padding: 2px 6px;
		border: 1px solid var(--ll-chicago-20);
		border-radius: 2px;
		font-family: monospace;
		font-size: 13px;
	}
	.save-btn, .cancel-btn {
		padding: 2px 6px;
		border: none;
		border-radius: 2px;
		cursor: pointer;
		font-size: 12px;
		background: transparent;
	}
	.save-btn {
		color: var(--ll-chicago-20);
	}
	.cancel-btn {
		color: var(--ll-red-42);
	}
</style>
