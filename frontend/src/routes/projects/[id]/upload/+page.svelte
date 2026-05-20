<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';

	let projectId = $derived($page.params.id);
	let file = $state<File | null>(null);
	let uploading = $state(false);
	let error = $state('');

	function handleFileChange(e: Event) {
		const input = e.target as HTMLInputElement;
		file = input.files?.[0] ?? null;
		error = '';
	}

	async function handleUpload() {
		if (!file) return;
		uploading = true;
		error = '';

		const formData = new FormData();
		formData.append('file', file);

		try {
			const res = await fetch(`/api/projects/${projectId}/upload`, {
				method: 'POST',
				body: formData
			});
			if (!res.ok) {
				const detail = await res.json();
				error = detail.detail || `Upload failed (${res.status})`;
				return;
			}
			const data = await res.json();
			if (data.all_values_mapped) {
				goto(`/projects/${projectId}/export?file_id=${data.file_id}`);
			} else {
				goto(`/projects/${projectId}/review?file_id=${data.file_id}`);
			}
		} catch (e) {
			error = 'Network error during upload';
		} finally {
			uploading = false;
		}
	}
</script>

<div class="upload-page">
	<header>
		<a href="/projects/{projectId}" class="back">← Back to Project</a>
		<h1>Upload File</h1>
		<p class="subtitle">Supported formats: CSV, XLSX, JSON, Parquet</p>
	</header>

	<div class="upload-area">
		<input
			type="file"
			accept=".csv,.xlsx,.json,.parquet"
			onchange={handleFileChange}
			disabled={uploading}
			id="file-input"
		/>
		<label for="file-input" class="file-label">
			{file ? file.name : 'Choose a file...'}
		</label>

		{#if file}
			<button onclick={handleUpload} disabled={uploading} class="upload-btn">
				{uploading ? 'Uploading...' : 'Upload & Analyze'}
			</button>
		{/if}
	</div>

	{#if error}
		<p class="error">{error}</p>
	{/if}
</div>

<style>
	.upload-page {
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
	.upload-area {
		display: flex;
		flex-direction: column;
		gap: 12px;
		padding: 24px;
		border: 2px dashed var(--ll-london-85);
		border-radius: 2px;
		background: white;
	}
	input[type='file'] {
		position: absolute;
		width: 1px;
		height: 1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
	}
	.file-label {
		padding: 12px 16px;
		border: 1px solid var(--ll-london-85);
		border-radius: 2px;
		cursor: pointer;
		font-size: 15px;
		color: var(--ll-london-35);
		text-align: center;
	}
	.file-label:hover {
		border-color: var(--ll-chicago-20);
		color: var(--ll-london-20);
	}
	.upload-btn {
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
	.upload-btn:hover:not(:disabled) {
		background: var(--ll-chicago-10);
	}
	.upload-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	.error {
		color: var(--ll-red-42);
		font-size: 14px;
		margin-top: 12px;
	}
</style>
