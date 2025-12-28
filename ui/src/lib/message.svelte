<script lang="ts">
	type Props = {
		role: "user" | "assistant";
		content: string;
		entities?: Record<string, string[]>;
	};

	let { role, content, entities }: Props = $props();
</script>

<div class="message {role}">
	<div class="avatar">
		{role === "user" ? "👤" : "🤖"}
	</div>
	<div class="content">
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
</div>

<style>
	.message {
		display: flex;
		gap: 0.75rem;
		padding: 1rem;
		border-bottom: 1px solid #e5e7eb;
	}
	.message.user {
		background: #f0f9ff;
	}
	.message.assistant {
		background: #f0fdf4;
	}
	.avatar {
		font-size: 1.5rem;
		flex-shrink: 0;
	}
	.name {
		font-weight: 600;
		font-size: 0.875rem;
		color: #374151;
	}
	.content {
		flex: 1;
	}
	.content p {
		margin: 0.25rem 0 0 0;
		line-height: 1.5;
	}
	.entities {
		margin-top: 0.5rem;
		display: flex;
		flex-wrap: wrap;
		gap: 0.25rem;
	}
	.entity-tag {
		background: #dbeafe;
		padding: 0.2rem 0.5rem;
		border-radius: 4px;
		font-size: 0.75rem;
		color: #1e40af;
	}
</style>
