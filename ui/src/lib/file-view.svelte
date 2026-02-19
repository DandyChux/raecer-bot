<script lang="ts">
	import { onMount } from "svelte";
	import { apiClient } from "./api";
	import { navigateToChat } from "./stores/router.svelte";
	import Button from "./components/ui/button/button.svelte";

	interface DataFile {
		name: string;
		size: number;
		modified: string;
	}
	let files: DataFile[] = [];
	let loading = true;
	let error = "";
	let expandedFile: string | null = null;
	let fileContents: Record<string, string> = {};
	let copiedFile: string | null = null;

	// Auth state
	let authenticated = false;
	let passwordInput = "";
	let authError = "";
	let authLoading = false;
	let adminToken = "";

	onMount(() => {
		// await loadFiles();
		const saved = sessionStorage.getItem("admin_token");
		if (saved) {
			adminToken = saved;
			authenticated = true;
			loadFiles();
		}
	});

	function authHeaders() {
		return {
			Authorization: `Bearer ${adminToken}`,
		};
	}

	async function handleLogin() {
		if (!passwordInput.trim()) return;
		authLoading = true;
		authError = "";

		try {
			await apiClient.post("/auth/verify", {
				password: passwordInput,
			});
			adminToken = passwordInput;
			sessionStorage.setItem("admin_token", adminToken);
			authenticated = true;
			passwordInput = "";
			await loadFiles();
		} catch (e: any) {
			if (e?.response?.status === 401) {
				authError = "Incorrect password";
			} else {
				authError = "Failed to authenticate. Please try again.";
			}
		} finally {
			authLoading = false;
		}
	}

	function handleLogout() {
		authenticated = false;
		adminToken = "";
		files = [];
		fileContents = {};
		expandedFile = null;
		sessionStorage.removeItem("admin_token");
	}

	function handleKeyDown(event: KeyboardEvent) {
		if (event.key === "Enter") {
			handleLogin();
		}
	}

	async function loadFiles() {
		loading = true;
		error = "";

		try {
			const { data } = await apiClient.get("/data/files", {
				headers: authHeaders(),
			});
			files = data.files;
		} catch (e: any) {
			if (e?.response?.status === 401) {
				handleLogout();
				authError = "Session expired. Please log in again.";
				return;
			}
			error = "Failed to load files.";
			console.error(e);
		} finally {
			loading = false;
		}
	}

	async function toggleFileContent(filename: string) {
		if (expandedFile === filename) {
			expandedFile = null;
			return;
		}

		if (!fileContents[filename]) {
			try {
				const { data } = await apiClient.get(
					`/data/files/${filename}/content`,
					{
						headers: authHeaders(),
					},
				);
				fileContents[filename] = JSON.stringify(data.content, null, 2);
			} catch (e) {
				console.error(e);
				fileContents[filename] = "Error loading file content";
			}

			// Trigger file content update
			fileContents = { ...fileContents };
		}

		expandedFile = filename;
	}

	async function copyContent(filename: string) {
		const content = fileContents[filename];
		if (!content) return;

		try {
			await navigator.clipboard.writeText(content);
			copiedFile = filename;
			setTimeout(() => {
				copiedFile = null;
			}, 2000);
		} catch (e) {
			console.error("Failed to copy: ", e);
		}
	}

	function downloadFile(filename: string) {
		apiClient
			.get(`/data/files/${filename}`, {
				headers: authHeaders(),
				responseType: "blob",
			})
			.then(({ data }) => {
				const url = URL.createObjectURL(data);
				const a = document.createElement("a");
				a.href = url;
				a.download = filename;
				a.click();
				URL.revokeObjectURL(url);
			})
			.catch((e) => console.error("Download failed: ", e));
	}

	function formatSize(bytes: number): string {
		if (bytes < 1024) return `${bytes} B`;
		return `${(bytes / 1024).toFixed(1)} KB`;
	}

	function formatDate(isoDate: string): string {
		return new Date(isoDate).toLocaleString();
	}

	function getFileType(
		filename: string,
	): "patient_summary" | "pro_ctcae" | "other" {
		if (filename.startsWith("patient_summary")) return "patient_summary";
		if (filename.startsWith("pro_ctcae")) return "pro_ctcae";
		return "other";
	}
</script>

<div class="files-view">
	{#if !authenticated}
		<!-- Password gate -->
		<div class="auth-gate">
			<div class="auth-card">
				<h2>🔒 Admin Access</h2>
				<p>Enter the admin password to view data files.</p>

				{#if authError}
					<div class="auth-error">{authError}</div>
				{/if}

				<div class="auth-form">
					<input
						type="password"
						bind:value={passwordInput}
						on:keydown={handleKeyDown}
						placeholder="Password"
						disabled={authLoading}
					/>
					<button
						class="btn btn-primary"
						on:click={handleLogin}
						disabled={authLoading || !passwordInput.trim()}
					>
						{authLoading ? "Verifying..." : "Login"}
					</button>
				</div>

				<button class="btn btn-link" on:click={navigateToChat}>
					← Back to Chat
				</button>
			</div>
		</div>
	{:else}
		<header>
			<h2>📁 Data Files</h2>
			<div class="header-actions">
				<Button variant="secondary" onclick={loadFiles}
					>🔄 Refresh</Button
				>
				<Button onclick={navigateToChat}>← Back to Chat</Button>
			</div>
		</header>

		{#if loading}
			<div class="loading-state">
				<div class="spinner"></div>
				<p>Loading files...</p>
			</div>
		{:else if error}
			<div class="error-state">
				<p>{error}</p>
				<Button onclick={loadFiles}>Retry</Button>
			</div>
		{:else if files.length === 0}
			<div class="empty-state">
				<p>No data files found.</p>
			</div>
		{:else}
			<p class="file-count">
				{files.length} file{files.length === 1 ? "" : "s"}
			</p>

			<div class="file-list">
				{#each files as file}
					{@const fileType = getFileType(file.name)}

					<div
						class="file-card"
						class:expanded={expandedFile === file.name}
					>
						<div class="file-info">
							<div class="file-name-row">
								<span
									class="file-badge"
									class:badge-patient={fileType ===
										"patient_summary"}
									class:badge-proctcae={fileType ===
										"pro_ctcae"}
								>
									{#if fileType === "patient_summary"}
										🏥 Patient Summary
									{:else if fileType === "pro_ctcae"}
										📊 PRO-CTCAE
									{:else}
										📄 Other
									{/if}
								</span>
							</div>
							<div class="file-meta">
								<span>{formatSize(file.size)}</span>
								<span>.</span>
								<span>{formatDate(file.modified)}</span>
							</div>
						</div>

						<div class="file-actions">
							<Button
								variant="outline"
								size="sm"
								onclick={() => toggleFileContent(file.name)}
							>
								{expandedFile === file.name ? "Hide" : "View"}
							</Button>
							<Button
								variant="outline"
								size="sm"
								onclick={() => downloadFile(file.name)}
							>
								⬇ Download
							</Button>
						</div>

						{#if expandedFile === file.name && fileContents[file.name]}
							<div class="file-content">
								<div class="content-header">
									<span>JSON Content</span>
									<Button
										size="sm"
										class="btn-copy"
										onclick={() => copyContent(file.name)}
									>
										{copiedFile === file.name
											? "✅ Copied!"
											: "📋 Copy"}
									</Button>
								</div>
								<pre>{fileContents[file.name]}</pre>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
	{/if}
</div>

<style>
	.files-view {
		max-width: 800px;
		margin: 0 auto;
	}

	/* Auth gate */
	.auth-gate {
		display: flex;
		justify-content: center;
		align-items: center;
		min-height: 50vh;
	}
	.auth-card {
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 12px;
		padding: 2rem;
		text-align: center;
		max-width: 400px;
		width: 100%;
	}
	.auth-card h2 {
		margin: 0 0 0.5rem 0;
	}
	.auth-card p {
		color: #6b7280;
		margin: 0 0 1.5rem 0;
	}
	.auth-form {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}
	.auth-form input {
		flex: 1;
		padding: 0.75rem 1rem;
		border: 1px solid #d1d5db;
		border-radius: 6px;
		font-size: 1rem;
	}
	.auth-form input:focus {
		outline: none;
		border-color: #3b82f6;
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}
	.auth-error {
		background: #fef2f2;
		color: #dc2626;
		padding: 0.75rem;
		border-radius: 6px;
		margin-bottom: 1rem;
		font-size: 0.875rem;
	}

	/* Header */
	header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
		flex-wrap: wrap;
		gap: 0.75rem;
	}
	header h2 {
		margin: 0;
	}
	.header-actions {
		display: flex;
		gap: 0.5rem;
	}
	.file-count {
		color: #6b7280;
		margin: 0 0 1rem 0;
		font-size: 0.875rem;
	}
	.file-list {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	.file-card {
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		padding: 1rem 1.25rem;
		transition: border-color 0.15s;
	}
	.file-card:hover {
		border-color: #d1d5db;
	}
	.file-card.expanded {
		border-color: #3b82f6;
	}
	.file-info {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		flex-wrap: wrap;
		gap: 0.5rem;
		margin-bottom: 0.75rem;
	}
	.file-name-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-wrap: wrap;
	}
	.file-name {
		font-weight: 500;
		font-size: 0.9rem;
		color: #111827;
		word-break: break-all;
	}
	.file-badge {
		font-size: 0.75rem;
		padding: 0.15rem 0.5rem;
		border-radius: 999px;
		font-weight: 500;
		white-space: nowrap;
	}
	.badge-patient {
		background: #dbeafe;
		color: #1e40af;
	}
	.badge-proctcae {
		background: #d1fae5;
		color: #065f46;
	}
	.file-meta {
		display: flex;
		gap: 0.35rem;
		font-size: 0.8rem;
		color: #9ca3af;
	}
	.file-actions {
		display: flex;
		gap: 0.5rem;
	}

	/* File content */
	.file-content {
		margin-top: 1rem;
		border-top: 1px solid #e5e7eb;
		padding-top: 1rem;
	}
	.content-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
		font-size: 0.8rem;
		color: #6b7280;
		font-weight: 600;
	}
	.file-content pre {
		background: #1f2937;
		color: #f9fafb;
		padding: 1rem;
		border-radius: 6px;
		overflow-x: auto;
		font-size: 0.8rem;
		line-height: 1.5;
		max-height: 400px;
		overflow-y: auto;
	}

	/* States */
	.loading-state,
	.empty-state,
	.error-state {
		text-align: center;
		padding: 3rem 1rem;
		color: #6b7280;
	}
	.spinner {
		width: 32px;
		height: 32px;
		border: 3px solid #e5e7eb;
		border-top-color: #3b82f6;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
		margin: 0 auto 1rem;
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
	.error-state {
		color: #dc2626;
	}
</style>
