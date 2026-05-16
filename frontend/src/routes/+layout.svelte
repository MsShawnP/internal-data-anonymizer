<script>
	let { children } = $props();
</script>

<svelte:head>
	<style>
		:global(body) {
			margin: 0;
			font-family: 'Source Sans 3', 'Source Sans Pro', 'Helvetica Neue', Helvetica, Arial, sans-serif;
			background: #f8f6f1;
			color: #2a2a2a;
		}
	</style>
</svelte:head>

<main>
	{@render children()}
</main>
