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
					<span
						class="col-anonymized clickable"
						onclick={() => startEdit(mapping.original, mapping.anonymized)}
						title="Click to edit"
					>
						{mapping.anonymized}
					</span>
				{/if}
			</div>
		{/each}
	</div>
</div>

<style>
	.mapping-table {
		border: 1px solid #e5e0d8;
		border-radius: 2px;
		background: white;
		max-height: 400px;
		overflow-y: auto;
	}
	.table-header {
		display: grid;
		grid-template-columns: 1fr 30px 1fr;
		padding: 8px 12px;
		border-bottom: 1px solid #e5e0d8;
		font-size: 12px;
		font-weight: 600;
		color: #6b6b6b;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		position: sticky;
		top: 0;
		background: #f8f6f1;
	}
	.table-body {
		font-size: 14px;
	}
	.table-row {
		display: grid;
		grid-template-columns: 1fr 30px 1fr;
		padding: 6px 12px;
		border-bottom: 1px solid #f0ece5;
		align-items: center;
	}
	.table-row:last-child {
		border-bottom: none;
	}
	.col-arrow {
		text-align: center;
		color: #6b6b6b;
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
	}
	.clickable:hover {
		background: #f0ece5;
	}
	.editing {
		display: flex;
		gap: 4px;
		align-items: center;
	}
	.editing input {
		flex: 1;
		padding: 2px 6px;
		border: 1px solid #1b3a5c;
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
		color: #1b3a5c;
	}
	.cancel-btn {
		color: #c54b4b;
	}
</style>
