<script lang="ts">
	import {
		currentView,
		navigateToChat,
		navigateToFiles,
	} from "$lib/stores/router.svelte";
	import Chat from "$lib/chat-view.svelte";
	import Results from "$lib/results-view.svelte";
	import Files from "$lib/file-view.svelte";
</script>

<main>
	<header>
		<div class="header-content">
			<div>
				<h1>🤖 RAECER</h1>
				<p>Medical History Assistant</p>
			</div>
			<nav>
				<button
					class="nav-btn"
					class:active={$currentView === "chat" ||
						$currentView === "results"}
					onclick={navigateToChat}
				>
					💬 Chat
				</button>
				<button
					class="nav-btn"
					class:active={$currentView === "files"}
					onclick={navigateToFiles}
				>
					📁 Files
				</button>
			</nav>
		</div>
	</header>

	<div class="container">
		{#if $currentView === "chat"}
			<Chat />
		{:else if $currentView === "results"}
			<Results />
		{:else if $currentView === "files"}
			<Files />
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
	}
	.header-content {
		max-width: 800px;
		margin: 0 auto;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	header h1 {
		margin: 0;
		font-size: 1.75rem;
	}
	header p {
		margin: 0.25rem 0 0 0;
		opacity: 0.9;
	}
	nav {
		display: flex;
		gap: 0.5rem;
	}
	.nav-btn {
		background: rgba(255, 255, 255, 0.15);
		color: white;
		border: 1px solid rgba(255, 255, 255, 0.3);
		padding: 0.5rem 1rem;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.875rem;
		font-weight: 500;
		transition: all 0.15s;
	}
	.nav-btn:hover {
		background: rgba(255, 255, 255, 0.25);
	}
	.nav-btn.active {
		background: rgba(255, 255, 255, 0.35);
		border-color: rgba(255, 255, 255, 0.5);
	}
	.container {
		max-width: 800px;
		margin: 0 auto;
		padding: 1.5rem;
		height: calc(100dvh - 120px);
	}
</style>
