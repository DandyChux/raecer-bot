<script lang="ts">
	type Props = {
		role: "user" | "assistant";
		content: string;
		entities?: Record<string, string[]>;
	};

	let { role, content, entities }: Props = $props();
</script>

<div class="message-row {role}">
	{#if role === "assistant"}
		<div class="avatar">🤖</div>
	{/if}
	<div class="bubble {role}">
		<span class="name">{role === "user" ? "You" : "Cornelius"}</span>
		<p>{content}</p>
		{#if entities && Object.keys(entities).length > 0}
			<div class="entities">
				{#each Object.entries(entities) as [type, values]}
					<span class="entity-tag">{type}: {values.join(", ")}</span>
				{/each}
			</div>
		{/if}
	</div>
	{#if role === "user"}
		<div class="avatar">👤</div>
	{/if}
</div>

<style>
	.message-row {
		display: flex;
		align-items: flex-end;
		padding: 0.25rem 1rem;
		gap: 0.5rem;
	}
	.message-row.user {
		justify-content: flex-end;
	}
	.message-row.assistant {
		justify-content: flex-start;
	}
	.avatar {
		font-size: 1.5rem;
		flex-shrink: 0;
		width: 2rem;
		height: 2rem;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.bubble {
		max-width: 70%;
		padding: 0.75rem 1rem;
		border-radius: 1.25rem;
		position: relative;
	}
	.bubble.user {
		background: #0b93f6;
		color: white;
		border-bottom-right-radius: 0.25rem;
	}
	.bubble.assistant {
		background: #e5e5ea;
		color: #1c1c1e;
		border-bottom-left-radius: 0.25rem;
	}
	.name {
		font-weight: 600;
		font-size: 0.7rem;
		opacity: 0.8;
		display: block;
		margin-bottom: 0.25rem;
	}
	.bubble.user .name {
		color: rgba(255, 255, 255, 0.85);
	}
	.bubble.assistant .name {
		color: #6b7280;
	}
	.bubble p {
		margin: 0;
		line-height: 1.4;
		font-size: 0.95rem;
	}
	.entities {
		margin-top: 0.5rem;
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem;
	}
	.entity-tag {
		padding: 0.15rem 0.5rem;
		border-radius: 0.75rem;
		font-size: 0.7rem;
	}
	.bubble.user .entity-tag {
		background: rgba(255, 255, 255, 0.25);
		color: white;
	}
	.bubble.assistant .entity-tag {
		background: #dbeafe;
		color: #1e40af;
	}
</style>
