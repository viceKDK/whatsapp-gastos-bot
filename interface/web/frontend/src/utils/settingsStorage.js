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

// Devuelve la tasa manual UYU por 1 USD (por defecto 40)
export function getFxUYUperUSD() {
  const s = getSettings()
  const raw = Number(s.fxUYUperUSD)
  if (!isFinite(raw) || raw <= 0) return 40
  return raw
}

export function isSafeMode() {
  const s = getSettings()
  return !!s.safeMode
}
