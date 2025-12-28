import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';
import path from "path";
import { svelte } from '@sveltejs/vite-plugin-svelte';

// https://vite.dev/config/
export default defineConfig({
	plugins: [tailwindcss(), svelte()],
	build: { outDir: "../static", emptyOutDir: true },

	server: {
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				secure: false
			}
		},
		port: 3000
	},

	resolve: {
		alias: {
			$lib: path.resolve("./src/lib"),
		},
	},
});
