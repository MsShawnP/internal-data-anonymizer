<script>
	let { children } = $props();
</script>

<svelte:head>
	<style>
		@font-face {
			font-family: 'Playfair Display';
			font-style: normal;
			font-weight: 400 700;
			font-display: swap;
			src: url('/fonts/playfair-display-latin.woff2') format('woff2');
			unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
		}
		@font-face {
			font-family: 'Playfair Display';
			font-style: normal;
			font-weight: 400 700;
			font-display: swap;
			src: url('/fonts/playfair-display-latin-ext.woff2') format('woff2');
			unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
		}
		@font-face {
			font-family: 'Source Sans 3';
			font-style: normal;
			font-weight: 400 700;
			font-display: swap;
			src: url('/fonts/source-sans-3-latin.woff2') format('woff2');
			unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
		}
		@font-face {
			font-family: 'Source Sans 3';
			font-style: normal;
			font-weight: 400 700;
			font-display: swap;
			src: url('/fonts/source-sans-3-latin-ext.woff2') format('woff2');
			unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF;
		}

		:root {
			--ll-canvas: #f5f3ee;
			--ll-red-42: #cc100a;
			--ll-red-95: #fce8e7;
			--ll-chicago-95: #e8eaf4;
			--ll-chicago-85: #c5cbe6;
			--ll-chicago-70: #8e9ad0;
			--ll-chicago-20: #1f2e7a;
			--ll-chicago-10: #141e52;
			--ll-chicago-5: #0a0f29;
			--ll-hk-35: #158f75;
			--ll-hk-95: #e4f5f0;
			--ll-tokyo-40: #b82d4a;
			--ll-sg-55: #ee8a2a;
			--ll-sg-95: #fdeee0;
			--ll-london-95: #f2f2f2;
			--ll-london-90: #e0e0e0;
			--ll-london-85: #d9d9d9;
			--ll-london-70: #b3b3b3;
			--ll-london-40: #666666;
			--ll-london-35: #595959;
			--ll-london-20: #333333;
			--ll-london-10: #1a1a1a;
			--ll-london-5: #0d0d0d;
			--ll-serif: 'Playfair Display', Georgia, 'Times New Roman', serif;
			--ll-sans: 'Source Sans 3', 'Source Sans Pro', 'Helvetica Neue', Helvetica, Arial, sans-serif;
			--ll-radius: 2px;
			--ll-max-width: 900px;
		}

		:global(body) {
			margin: 0;
			font-family: var(--ll-sans);
			background: var(--ll-canvas);
			color: var(--ll-london-20);
			line-height: 1.6;
		}
	</style>
</svelte:head>

<main>
	{@render children()}
</main>
