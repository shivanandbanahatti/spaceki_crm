import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const spacekiSrc = path.resolve(__dirname, 'src')
const crmFrontend = path.resolve(__dirname, '../../crm/frontend')
const crmSrc = path.resolve(crmFrontend, 'src')
const crmEntry = path.join(crmSrc, 'main.js')

function crmDependencyAliases() {
	const aliases = {}
	const frappeUiRoot = path.resolve(crmFrontend, 'node_modules/frappe-ui')
	if (fs.existsSync(frappeUiRoot)) {
		aliases['frappe-ui/tailwind'] = path.join(frappeUiRoot, 'tailwind/preset.js')
		aliases['frappe-ui/style.css'] = path.join(frappeUiRoot, 'src/style.css')
		aliases['frappe-ui/frappe'] = path.join(frappeUiRoot, 'frappe/index.js')
		aliases['frappe-ui'] = path.join(frappeUiRoot, 'src/index.ts')
	}
	return aliases
}

/** Vite aliases for Spaceki CRM UI overrides (loaded by FCRM vite.config). */
export function extendViteConfig(config) {
	config.resolve.alias = {
		...crmDependencyAliases(),
		'@spaceki': spacekiSrc,
		'@/pages/Deals.vue': path.resolve(spacekiSrc, 'pages/Deals.vue'),
		'@/composables/useRelatedCounts': path.resolve(
			spacekiSrc,
			'composables/useRelatedCounts.js',
		),
		'@/composables/useRelatedCounts.js': path.resolve(
			spacekiSrc,
			'composables/useRelatedCounts.js',
		),
		'@': crmSrc,
	}

	config.plugins.push({
		name: 'spaceki-crm-resolve',
		enforce: 'pre',
		async resolveId(source, importer, options) {
			if (!importer?.includes('spaceki_crm')) return null
			if (source.startsWith('.') || source.startsWith('/') || source.startsWith('\0')) {
				return null
			}
			if (source.startsWith('@/') || source.startsWith('@spaceki')) {
				return null
			}

			const resolved = await this.resolve(source, crmEntry, {
				...options,
				skipSelf: true,
			})
			return resolved?.id ?? null
		},
	})

	const benchRoot = path.resolve(__dirname, '../../..')
	config.server.fs.allow = [...(config.server.fs?.allow || []), benchRoot]
}

export function spacekiFrontendEnabled() {
	return fs.existsSync(path.resolve(__dirname, 'src/pages/Deals.vue'))
}
