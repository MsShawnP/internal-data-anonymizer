<script lang="ts">
	interface Props {
		detectedType: string;
		sampleValues: string[];
		onApply: (pattern: string) => void;
	}

	let { detectedType, sampleValues, onApply }: Props = $props();

	let mode = $derived<'word' | 'character'>(
		['name', 'email'].includes(detectedType) ? 'word' : 'character'
	);

	let pattern = $state('');
	let preview = $derived(generatePreview(pattern, mode));

	const WORD_CATEGORIES = ['Adjective', 'Noun', 'Verb', 'Color', 'Animal', 'City'];
	const CHAR_CLASSES = [
		{ label: 'A', desc: 'Uppercase letter' },
		{ label: 'a', desc: 'Lowercase letter' },
		{ label: '9', desc: 'Digit' },
		{ label: '-', desc: 'Literal hyphen' },
		{ label: '_', desc: 'Literal underscore' },
		{ label: ' ', desc: 'Space' }
	];

	function generatePreview(pat: string, m: 'word' | 'character'): string {
		if (!pat) return '';
		if (m === 'word') {
			return pat.replace(/\[(\w+)\]/g, (_, cat) => `<${cat}>`);
		}
		return pat
			.replace(/A/g, 'X')
			.replace(/a/g, 'x')
			.replace(/9/g, '0');
	}

	function insertWordCategory(cat: string) {
		pattern += `[${cat}] `;
	}

	function insertCharClass(cls: string) {
		pattern += cls;
	}

	function handleApply() {
		if (pattern.trim()) {
			onApply(pattern.trim());
		}
	}
</script>

<div class="pattern-editor">
	<h3>Bulk Pattern Rule</h3>
	<p class="description">
		{#if mode === 'word'}
			Build a template using word categories. All values will be regenerated matching this pattern.
		{:else}
			Define a character-class pattern. A=letter, 9=digit, other chars are literal.
		{/if}
	</p>

	{#if sampleValues.length > 0}
		<div class="samples">
			<span class="samples-label">Sample values:</span>
			{#each sampleValues.slice(0, 3) as val}
				<code>{val}</code>
			{/each}
		</div>
	{/if}

	<div class="palette">
		{#if mode === 'word'}
			{#each WORD_CATEGORIES as cat}
				<button class="palette-btn" onclick={() => insertWordCategory(cat)}>
					[{cat}]
				</button>
			{/each}
			<button class="palette-btn" onclick={() => { pattern += '[4-digit] '; }}>
				[4-digit]
			</button>
		{:else}
			{#each CHAR_CLASSES as cls}
				<button
					class="palette-btn"
					onclick={() => insertCharClass(cls.label)}
					title={cls.desc}
				>
					{cls.label === ' ' ? '␣' : cls.label}
				</button>
			{/each}
		{/if}
	</div>

	<div class="input-row">
		<input
			type="text"
			bind:value={pattern}
			placeholder={mode === 'word' ? '[Adjective] [Noun] [4-digit]' : 'AA-9999-A'}
		/>
		<button class="clear-btn" onclick={() => { pattern = ''; }}>Clear</button>
	</div>

	{#if preview}
		<div class="preview">
			<span class="preview-label">Preview:</span>
			<code>{preview}</code>
		</div>
	{/if}

	<button class="apply-btn" onclick={handleApply} disabled={!pattern.trim()}>
		Apply Pattern to All Values
	</button>
</div>

<style>
	.pattern-editor {
		border: 1px solid var(--ll-london-85);
		border-radius: 2px;
		padding: 16px;
		background: white;
		margin-top: 12px;
	}
	h3 {
		font-size: 14px;
		font-weight: 600;
		margin: 0 0 4px;
	}
	.description {
		font-size: 13px;
		color: var(--ll-london-35);
		margin: 0 0 12px;
	}
	.samples {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 12px;
		flex-wrap: wrap;
	}
	.samples-label {
		font-size: 12px;
		color: var(--ll-london-35);
	}
	.samples code {
		font-size: 12px;
		background: var(--ll-canvas);
		padding: 2px 6px;
		border-radius: 2px;
		border: 1px solid var(--ll-london-85);
	}
	.palette {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
		margin-bottom: 12px;
	}
	.palette-btn {
		padding: 4px 8px;
		border: 1px solid var(--ll-london-85);
		border-radius: 2px;
		background: var(--ll-canvas);
		cursor: pointer;
		font-family: monospace;
		font-size: 12px;
	}
	.palette-btn:hover {
		border-color: var(--ll-chicago-20);
		background: white;
	}
	.input-row {
		display: flex;
		gap: 8px;
		margin-bottom: 12px;
	}
	.input-row input {
		flex: 1;
		padding: 6px 10px;
		border: 1px solid var(--ll-london-85);
		border-radius: 2px;
		font-family: monospace;
		font-size: 14px;
	}
	.input-row input:focus {
		outline: none;
		border-color: var(--ll-chicago-20);
	}
	.clear-btn {
		padding: 6px 12px;
		border: 1px solid var(--ll-london-85);
		border-radius: 2px;
		background: white;
		cursor: pointer;
		font-size: 13px;
	}
	.clear-btn:hover {
		border-color: var(--ll-red-42);
		color: var(--ll-red-42);
	}
	.preview {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 12px;
	}
	.preview-label {
		font-size: 12px;
		color: var(--ll-london-35);
	}
	.preview code {
		font-size: 13px;
		background: var(--ll-canvas);
		padding: 2px 8px;
		border-radius: 2px;
	}
	.apply-btn {
		width: 100%;
		padding: 8px 16px;
		background: var(--ll-chicago-20);
		color: white;
		border: none;
		border-radius: 2px;
		font-family: inherit;
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
	}
	.apply-btn:hover:not(:disabled) {
		background: var(--ll-chicago-10);
	}
	.apply-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
</style>
