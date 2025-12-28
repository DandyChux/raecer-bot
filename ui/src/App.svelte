<script lang="ts">
	import { currentView } from "$lib/stores/router.svelte";
	import Chat from "$lib/chat-view.svelte";
	import Results from "$lib/results-view.svelte";
	import { Bot } from "@lucide/svelte";
</script>

<main>
	<header>
		<h1>🤖 RAECER</h1>
		<p>Medical History Assistant</p>
	</header>

	<div class="container">
		{#if $currentView === "chat"}
			<Chat />
		{:else}
			<Results />
		{/if}
	</div>
</main>

<style>
	main {
		min-height: 100dvh;
		background: var(--color-background);
	}
	header {
		background: linear-gradient(
			135deg,
			var(--color-amber-700) 0%,
			var(--color-blue-600) 100%
		);
		color: white;
		padding: 1.5rem;
		text-align: center;
	}
	header h1 {
		margin: 0;
		font-size: 1.75rem;
	}
	header p {
		margin: 0.25rem 0 0 0;
		opacity: 0.9;
	}
	.container {
		max-width: 800px;
		margin: 0 auto;
		padding: 1.5rem;
		height: calc(100dvh - 120px);
	}
</style>
