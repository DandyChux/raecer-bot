<script lang="ts">
	import { Button } from "./components/ui/button";
	import { summaryData, navigateToChat } from "./stores/router.svelte";

	$: patientData = $summaryData?.patient_data;
	$: proCtcaeData = $summaryData?.pro_ctcae_data;
</script>

<div class="results">
	<div class="header">
		<h2>📋 Patient Summary</h2>
		<Button onclick={navigateToChat}>Start New Conversation</Button>
	</div>

	{#if patientData}
		<section class="card">
			<h3>Patient Information</h3>
			<div class="grid">
				<div class="field">
					<span class="field-label"
						>Previous Reaction to Contrast</span
					>
					<span
						class="value {patientData.has_previous_reaction
							? 'warning'
							: 'ok'}"
					>
						{patientData.has_previous_reaction ? "Yes" : "No"}
					</span>
				</div>
				<div class="field">
					<span class="field-label">Kidney Issues</span>
					<span
						class="value {patientData.has_kidney_issues
							? 'warning'
							: 'ok'}"
					>
						{patientData.has_kidney_issues ? "Yes" : "No"}
					</span>
				</div>
				<div class="field">
					<span class="field-label">Takes Metformin</span>
					<span
						class="value {patientData.takes_metformin
							? 'warning'
							: 'ok'}"
					>
						{patientData.takes_metformin ? "Yes" : "No"}
					</span>
				</div>
			</div>

			{#if Array.isArray(patientData.reported_symptoms) && patientData.reported_symptoms.length}
				<div class="section">
					<span class="field-label">Reported Symptoms</span>
					<ul>
						{#each patientData.reported_symptoms as symptom}
							<li>{symptom}</li>
						{/each}
					</ul>
				</div>
			{/if}

			{#if Array.isArray(patientData.patient_concerns) && patientData.patient_concerns.length}
				<div class="section">
					<span class="field-label">Patient Concerns</span>
					<ul>
						{#each patientData.patient_concerns as concern}
							<li>{concern}</li>
						{/each}
					</ul>
				</div>
			{/if}

			{#if patientData.full_summary}
				<div class="section">
					<span class="field-label">Full Summary</span>
					<p class="summary-text">{patientData.full_summary}</p>
				</div>
			{/if}
		</section>
	{/if}

	{#if proCtcaeData}
		<section class="card">
			<h3>PRO-CTCAE Mapping</h3>
			{#if proCtcaeData.clinical_summary}
				<p class="clinical-summary">{proCtcaeData.clinical_summary}</p>
			{/if}
			{#if Array.isArray(proCtcaeData.entries) && proCtcaeData.entries.length}
				<div class="symptoms">
					{#each proCtcaeData.entries as entry}
						{#if typeof entry === "object" && Object.keys(entry).length > 0}
							<div class="symptom-card">
								<span class="symptom-term"
									>{entry.symptom_term}</span
								>
								<span class="symptom-code">{entry.code}</span>
								{#if entry.severity}
									<span class="severity"
										>Severity: {entry.severity.label}</span
									>
								{/if}
							</div>
						{/if}
					{/each}
				</div>
			{/if}
		</section>
	{/if}

	<details class="raw-data">
		<summary>View Raw JSON</summary>
		<pre>{JSON.stringify($summaryData, null, 2)}</pre>
	</details>
</div>

<style>
	.results {
		max-width: 800px;
		margin: 0 auto;
	}
	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1.5rem;
	}
	.header h2 {
		margin: 0;
	}
	.card {
		background: white;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		padding: 1.5rem;
		margin-bottom: 1rem;
	}
	.card h3 {
		margin: 0 0 1rem 0;
		color: #111827;
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 1rem;
	}
	.field label {
		display: block;
		font-size: 0.875rem;
		color: #6b7280;
		margin-bottom: 0.25rem;
	}
	.value {
		font-weight: 600;
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
	}
	.value.ok {
		background: #d1fae5;
		color: #065f46;
	}
	.value.warning {
		background: #fef3c7;
		color: #92400e;
	}
	.section {
		margin-top: 1rem;
	}
	.section label {
		font-weight: 600;
		color: #374151;
	}
	.section ul {
		margin: 0.5rem 0;
		padding-left: 1.5rem;
	}
	.summary-text {
		background: #f9fafb;
		padding: 1rem;
		border-radius: 6px;
		line-height: 1.6;
	}
	.clinical-summary {
		background: #ecfdf5;
		padding: 1rem;
		border-radius: 6px;
		color: #065f46;
	}
	.symptoms {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		margin-top: 1rem;
	}
	.symptom-card {
		background: #f3f4f6;
		padding: 0.5rem 1rem;
		border-radius: 6px;
	}
	.symptom-term {
		font-weight: 600;
	}
	.symptom-code {
		color: #6b7280;
		margin-left: 0.5rem;
	}
	.severity {
		display: block;
		font-size: 0.875rem;
		color: #dc2626;
	}
	.raw-data {
		margin-top: 1rem;
	}
	.raw-data summary {
		cursor: pointer;
		color: #6b7280;
	}
	.raw-data pre {
		background: #1f2937;
		color: #f9fafb;
		padding: 1rem;
		border-radius: 6px;
		overflow-x: auto;
		font-size: 0.875rem;
	}
</style>
