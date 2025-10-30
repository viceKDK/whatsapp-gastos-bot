const KEY = 'app_settings'

export function getSettings() {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return {}
    return JSON.parse(raw)
  } catch {
    return {}
  }
}

export function saveSettings(settings) {
  try {
    localStorage.setItem(KEY, JSON.stringify(settings))
  } catch {}
}

export function getLanguage() {
  const s = getSettings()
  return s.language || 'es'
}

export function getCurrency() {
  const s = getSettings()
  return s.currency || 'UYU'
}

export function isSafeMode() {
  const s = getSettings()
  return !!s.safeMode
}

