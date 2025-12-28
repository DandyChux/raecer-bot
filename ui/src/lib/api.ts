import axios, { AxiosError, type AxiosRequestConfig } from 'axios';

export const API_BASE_URL = import.meta.env.VITE_API_URL;

export const apiClient = axios.create({
	// baseURL: `${API_BASE_URL}/api`,
	baseURL: '/api', // Vite proxy will resolve to proper URL
	headers: {
		'Content-Type': 'application/json'
	}
});

// Generic request function for React Query
export async function apiRequest<T>(
	config: AxiosRequestConfig
): Promise<T> {
	try {
		const response = await apiClient(config);
		return response.data as T;
	} catch (error) {
		const axiosError = error as AxiosError;
		// Handle specific cases here
		throw axiosError;
	}
}

// =============================
//  API request/response types
// =============================
export interface ConversationSession {
	session_id: string;
	message: string;
	status: string;
}

export interface MessageResponse {
	response: string;
	entities: Record<string, string[]>;
	conversation_ended: boolean;
	message_count: number;
}

export interface Summary {
	patient_data: PatientData;
	pro_ctcae_data: ProCTCAEData;
}

export interface PatientData {
	has_previous_reaction: boolean;
	has_kidney_issues: boolean;
	takes_metformin: boolean;
	reported_symptoms: string[];
	patient_concerns: string;
	full_summary: string;
}

export interface ProCTCAEData {
	pro_ctcae_version: string;
	assessment_date: string;
	entries: Record<string, any>[];
	source_file: string;
	clinical_summary: string;
}
