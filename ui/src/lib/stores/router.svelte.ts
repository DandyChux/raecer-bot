import { writable } from 'svelte/store';
import type { Summary } from '$lib/api';

export type View = 'chat' | 'results';

export const currentView = writable<View>('chat');
export const sessionId = writable<string | null>(null);
export const summaryData = writable<Summary | null>(null);

export function navigateToResults(summary: Summary) {
	summaryData.set(summary);
	currentView.set('results');
}

export function navigateToChat() {
	summaryData.set(null);
	sessionId.set(null);
	currentView.set('chat');
}
