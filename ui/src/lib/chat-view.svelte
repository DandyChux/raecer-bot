<script lang="ts">
	import { onMount } from "svelte";
	import { apiClient, type ConversationSession } from "./api";
	import { sessionId, navigateToResults } from "./stores/router.svelte";
	import Message from "./message.svelte";

	type ChatMessage = {
		role: "user" | "assistant";
		content: string;
		entities?: Record<string, string[]>;
	};

	let messages: ChatMessage[] = [];
	let inputValue = "";
	let loading = false;
	let error = "";
	let chatContainer: HTMLDivElement;

	onMount(async () => {
		try {
			const { data: session } = await apiClient.post<ConversationSession>(
				"/conversation/start",
			);
			sessionId.set(session.session_id);
			messages = [{ role: "assistant", content: session.message }];
		} catch (e) {
			error =
				"Failed to connect to server. Make sure the API is running.";
		}
	});

	function scrollToBottom() {
		if (chatContainer) {
			chatContainer.scrollTop = chatContainer.scrollHeight;
		}
	}

	async function handleSend() {
		const sid = $sessionId;
		if (!inputValue.trim() || !sid || loading) return;

		const userMessage = inputValue.trim();
		inputValue = "";
		messages = [...messages, { role: "user", content: userMessage }];
		loading = true;
		error = "";

		setTimeout(scrollToBottom, 0);

		try {
			// const response = await sendMessage(sid, userMessage);
			const { data: response } = await apiClient.post(
				`/conversation/${sid}/message`,
				{ message: userMessage },
			);
			messages = [
				...messages,
				{
					role: "assistant",
					content: response.response,
					entities: response.entities,
				},
			];

			if (response.conversation_ended) {
				await handleEnd();
			}
		} catch (e) {
			error = "Failed to send message. Please try again.";
			console.error(e);
		} finally {
			loading = false;
			setTimeout(scrollToBottom, 0);
		}
	}

	async function handleEnd() {
		const sid = $sessionId;
		if (!sid) return;
		loading = true;

		try {
			const result = await apiClient.post(`/conversation/${sid}/end`);
			navigateToResults(result.data);
		} catch (e) {
			error = "Failed to generate summary.";
			loading = false;
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === "Enter" && !event.shiftKey) {
			event.preventDefault();
			handleSend();
		}
	}
</script>

<div class="chat-wrapper">
	<div class="chat-container" bind:this={chatContainer}>
		{#each messages as message}
			<Message
				role={message.role}
				content={message.content}
				entities={message.entities}
			/>
		{/each}
		{#if loading}
			<div class="loading">
				<span class="dot"></span><span class="dot"></span><span
					class="dot"
				></span>
			</div>
		{/if}
	</div>

	{#if error}
		<div class="error">{error}</div>
	{/if}

	<div class="input-area">
		<input
			bind:value={inputValue}
			on:keydown={handleKeydown}
			placeholder="Type your message..."
			disabled={loading}
		/>
		<button on:click={handleSend} disabled={loading || !inputValue.trim()}
			>Send</button
		>
		<button on:click={handleEnd} disabled={loading} class="end-btn"
			>End & Summarize</button
		>
	</div>
</div>

<style>
	.chat-wrapper {
		display: flex;
		flex-direction: column;
		height: 100%;
	}
	.chat-container {
		flex: 1;
		overflow-y: auto;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		margin-bottom: 1rem;
	}
	.input-area {
		display: flex;
		gap: 0.5rem;
	}
	input {
		flex: 1;
		padding: 0.75rem 1rem;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		font-size: 1rem;
	}
	input:focus {
		outline: none;
		border-color: #3b82f6;
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}
	button {
		padding: 0.75rem 1.5rem;
		background: #3b82f6;
		color: white;
		border: none;
		border-radius: 6px;
		cursor: pointer;
		font-size: 1rem;
		font-weight: 500;
	}
	button:hover:not(:disabled) {
		background: #2563eb;
	}
	button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	.end-btn {
		background: #10b981;
	}
	.end-btn:hover:not(:disabled) {
		background: #059669;
	}
	.loading {
		padding: 1rem;
		display: flex;
		gap: 0.25rem;
		justify-content: center;
	}
	.dot {
		width: 8px;
		height: 8px;
		background: var(--color-muted-foreground);
		border-radius: 50%;
		animation: bounce 1.4s infinite ease-in-out both;
	}
	.dot:nth-child(1) {
		animation-delay: -0.32s;
	}
	.dot:nth-child(2) {
		animation-delay: -0.16s;
	}
	@keyframes bounce {
		0%,
		80%,
		100% {
			transform: scale(0);
		}
		40% {
			transform: scale(1);
		}
	}
	.error {
		background: #fef2f2;
		color: #dc2626;
		padding: 0.75rem;
		border-radius: 6px;
		margin-bottom: 1rem;
	}
</style>
