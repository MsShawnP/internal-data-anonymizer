<script lang="ts">
	interface Props {
		binEdges: number[];
		originalCounts: number[];
		jitteredCounts: number[];
		stats: {
			original_mean: number;
			original_std: number;
			jittered_mean: number;
			jittered_std: number;
		};
	}

	let { binEdges, originalCounts, jitteredCounts, stats }: Props = $props();

	const WIDTH = 400;
	const HEIGHT = 120;
	const PADDING = { top: 10, right: 10, bottom: 20, left: 35 };
	const chartWidth = WIDTH - PADDING.left - PADDING.right;
	const chartHeight = HEIGHT - PADDING.top - PADDING.bottom;

	let maxCount = $derived(Math.max(...originalCounts, ...jitteredCounts, 1));

	function barX(index: number): number {
		return PADDING.left + (index / originalCounts.length) * chartWidth;
	}

	function barWidth(): number {
		return (chartWidth / originalCounts.length) * 0.4;
	}

	function barHeight(count: number): number {
		return (count / maxCount) * chartHeight;
	}

	function barY(count: number): number {
		return PADDING.top + chartHeight - barHeight(count);
	}
</script>

<div class="histogram-container">
	<svg viewBox="0 0 {WIDTH} {HEIGHT}" class="histogram-svg">
		<!-- Grid lines -->
		{#each [0.25, 0.5, 0.75, 1.0] as tick}
			<line
				x1={PADDING.left}
				y1={PADDING.top + chartHeight * (1 - tick)}
				x2={WIDTH - PADDING.right}
				y2={PADDING.top + chartHeight * (1 - tick)}
				stroke="var(--ll-london-85)"
				stroke-width="0.5"
			/>
		{/each}

		<!-- Original bars -->
		{#each originalCounts as count, i}
			<rect
				x={barX(i)}
				y={barY(count)}
				width={barWidth()}
				height={barHeight(count)}
				fill="var(--ll-chicago-70)"
				opacity="0.7"
			/>
		{/each}

		<!-- Jittered bars -->
		{#each jitteredCounts as count, i}
			<rect
				x={barX(i) + barWidth()}
				y={barY(count)}
				width={barWidth()}
				height={barHeight(count)}
				fill="var(--ll-chicago-20)"
				opacity="0.7"
			/>
		{/each}

		<!-- X-axis -->
		<line
			x1={PADDING.left}
			y1={PADDING.top + chartHeight}
			x2={WIDTH - PADDING.right}
			y2={PADDING.top + chartHeight}
			stroke="var(--ll-london-20)"
			stroke-width="0.5"
		/>
	</svg>

	<div class="legend">
		<span class="legend-item">
			<span class="swatch" style="background: var(--ll-chicago-70);"></span>
			Original (μ={stats.original_mean.toFixed(1)}, σ={stats.original_std.toFixed(1)})
		</span>
		<span class="legend-item">
			<span class="swatch" style="background: var(--ll-chicago-20);"></span>
			Jittered (μ={stats.jittered_mean.toFixed(1)}, σ={stats.jittered_std.toFixed(1)})
		</span>
	</div>
</div>

<style>
	.histogram-container {
		margin: 8px 0;
	}
	.histogram-svg {
		width: 100%;
		max-width: 400px;
		height: auto;
	}
	.legend {
		display: flex;
		gap: 16px;
		font-size: 11px;
		color: var(--ll-london-35);
		margin-top: 4px;
	}
	.legend-item {
		display: flex;
		align-items: center;
		gap: 4px;
	}
	.swatch {
		width: 10px;
		height: 10px;
		border-radius: 1px;
		display: inline-block;
	}
</style>
