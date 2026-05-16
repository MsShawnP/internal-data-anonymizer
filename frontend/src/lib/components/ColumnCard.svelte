<script lang="ts">
	import { STRATEGIES, type ColumnProfile, type Strategy } from '$lib/api';

	let {
		column,
		onconfirm
	}: {
		column: ColumnProfile;
		onconfirm: (strategy: Strategy) => void;
	} = $props();

	let selectedStrategy = $state<Strategy>(column.strategy as Strategy);
</script>

<div class="column-card">
	<div class="card-header">
		<h3 class="column-name">{column.name}</h3>
		<span class="detected-type">{column.detected_type}</span>
	</div>

	<div class="card-body">
		<div class="profile-row">
			<span class="label">Data type</span>
			<span class="value">{column.dtype}</span>
		</div>
		<div class="profile-row">
			<span class="label">Unique values</span>
			<span class="value">{column.unique_count.toLocaleString()}</span>
		</div>
		<div class="profile-row">
			<span class="label">Null rate</span>
			<span class="value">{(column.null_rate * 100).toFixed(1)}%</span>
		</div>

		{#if Object.keys(column.stats).length > 0}
			<div class="stats-section">
				<span class="label">Statistics</span>
				<div class="stats-grid">
					{#each Object.entries(column.stats) as [key, val]}
						<span class="stat-item">
							<span class="stat-key">{key}</span>
							<span class="stat-val">{typeof val === 'number' ? val.toLocaleString() : val}</span>
						</span>
					{/each}
				</div>
			</div>
		{/if}

		{#if column.sample_values.length > 0}
			<div class="samples-section">
				<span class="label">Sample values</span>
				<div class="samples-list">
					{#each column.sample_values as sample}
						<code class="sample-value">{sample}</code>
					{/each}
				</div>
			</div>
		{/if}
	</div>

	<div class="card-footer">
		<div class="strategy-selector">
			<label for="strategy-select" class="label">Strategy</label>
			<select
				id="strategy-select"
				bind:value={selectedStrategy}
			>
				{#each STRATEGIES as strat}
					<option value={strat}>{strat}</option>
				{/each}
			</select>
			{#if selectedStrategy !== column.strategy}
				<span class="override-indicator">overridden</span>
			{/if}
		</div>
		<button class="confirm-btn" onclick={() => onconfirm(selectedStrategy)}>
			Confirm
		</button>
	</div>
</div>

<style>
	.column-card {
		border: 1px solid #d8d4c8;
		border-radius: 2px;
		background: white;
		max-width: 560px;
		margin: 0 auto;
	}
	.card-header {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		padding: 16px 20px;
		border-bottom: 1px solid #e5e0d8;
	}
	.column-name {
		font-family: 'Playfair Display', Georgia, serif;
		font-size: 20px;
		font-weight: 700;
		margin: 0;
	}
	.detected-type {
		font-size: 13px;
		color: #6b6b6b;
		background: #f8f6f1;
		padding: 2px 8px;
		border-radius: 2px;
		border: 1px solid #e5e0d8;
	}
	.card-body {
		padding: 16px 20px;
	}
	.profile-row {
		display: flex;
		justify-content: space-between;
		padding: 6px 0;
		border-bottom: 1px solid #f0ede7;
	}
	.profile-row:last-child {
		border-bottom: none;
	}
	.label {
		font-size: 14px;
		color: #6b6b6b;
	}
	.value {
		font-size: 14px;
		font-weight: 600;
	}
	.stats-section,
	.samples-section {
		margin-top: 12px;
		padding-top: 12px;
		border-top: 1px solid #e5e0d8;
	}
	.stats-grid {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		margin-top: 6px;
	}
	.stat-item {
		display: flex;
		flex-direction: column;
		font-size: 13px;
		background: #f8f6f1;
		padding: 4px 8px;
		border-radius: 2px;
	}
	.stat-key {
		color: #6b6b6b;
		font-size: 11px;
		text-transform: uppercase;
	}
	.stat-val {
		font-weight: 600;
	}
	.samples-list {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin-top: 6px;
	}
	.sample-value {
		font-size: 13px;
		background: #f8f6f1;
		padding: 2px 8px;
		border-radius: 2px;
		border: 1px solid #e5e0d8;
		font-family: monospace;
	}
	.card-footer {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 16px 20px;
		border-top: 1px solid #e5e0d8;
		background: #fcfbf9;
	}
	.strategy-selector {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	select {
		padding: 6px 10px;
		border: 1px solid #d8d4c8;
		border-radius: 2px;
		font-family: inherit;
		font-size: 14px;
		background: white;
	}
	select:focus {
		outline: 2px solid #2a2a2a;
		outline-offset: 2px;
	}
	.override-indicator {
		font-size: 12px;
		color: #c54b4b;
		font-weight: 600;
	}
	.confirm-btn {
		padding: 8px 20px;
		background: #1b3a5c;
		color: white;
		border: none;
		border-radius: 2px;
		font-family: inherit;
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
	}
	.confirm-btn:hover {
		background: #14304b;
	}
</style>
