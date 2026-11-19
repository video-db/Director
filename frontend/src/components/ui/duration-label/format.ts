// Formatting and parsing of lengths in seconds, shared by Duration Label, Timestamp and the players.

// Non-finite input counts as 0: NaN is video.duration before metadata, Infinity a live stream.
function parts(totalSeconds: number) {
  const s = Number.isFinite(totalSeconds) ? Math.max(0, Math.round(totalSeconds)) : 0
  return { h: Math.floor(s / 3600), m: Math.floor((s % 3600) / 60), sec: s % 60 }
}

/** 75 → "01:15", 3725 → "1:02:05" */
export function formatDuration(totalSeconds: number) {
  const { h, m, sec } = parts(totalSeconds)
  const pad = (n: number) => String(n).padStart(2, '0')
  return h ? `${h}:${pad(m)}:${pad(sec)}` : `${pad(m)}:${pad(sec)}`
}

/** For screen readers, e.g. aria-valuetext: 75 → "1 minute 15 seconds", 3720 → "1 hour 2 minutes", 0 → "0 seconds" */
export function formatSpokenDuration(totalSeconds: number) {
  const { h, m, sec } = parts(totalSeconds)
  const unit = (n: number, word: string) => `${n} ${word}${n === 1 ? '' : 's'}`
  const spoken = [h && unit(h, 'hour'), m && unit(m, 'minute'), sec && unit(sec, 'second')].filter(Boolean)
  return spoken.length ? spoken.join(' ') : '0 seconds'
}

/** ISO 8601 duration for <time datetime>: 75 → "PT1M15S", 3725 → "PT1H2M5S", 0 → "PT0S" */
export function formatIsoDuration(totalSeconds: number) {
  const { h, m, sec } = parts(totalSeconds)
  const body = `${h ? `${h}H` : ''}${m ? `${m}M` : ''}${sec ? `${sec}S` : ''}`
  return `PT${body || '0S'}`
}

/** "01:15" or "1:02:05" → seconds; undefined for anything else, such as "LIVE" */
export function parseDuration(text: string) {
  if (!/^\d+(?::\d{1,2}){1,2}$/.test(text.trim())) return undefined
  return text.trim().split(':').reduce((total, n) => total * 60 + Number(n), 0)
}
