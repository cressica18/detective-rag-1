import { type ClassValue, clsx } from 'clsx'

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs)
}

/** Format a confidence float (0–1) to a percent string */
export function fmtConfidence(score: number): string {
  return `${Math.round(score * 100)}%`
}

/** Format score (0–100) to display string */
export function fmtScore(score: number): string {
  return score.toFixed(0)
}

/** Derive a doc-type label from a filename */
export function inferDocType(filename: string): string {
  const f = filename.toLowerCase()
  if (f.includes('police_report')) return 'POLICE REPORT'
  if (f.includes('witness_statement')) return 'WITNESS STMT'
  if (f.includes('suspect_interview')) return 'SUSPECT INTV'
  if (f.includes('cctv') || f.includes('transcript')) return 'CCTV TRANSCRIPT'
  if (f.includes('forensic')) return 'FORENSIC REPORT'
  if (f.includes('autopsy')) return 'AUTOPSY REPORT'
  if (f.includes('phone_records')) return 'PHONE RECORDS'
  if (f.includes('security_log') || f.includes('badge')) return 'SECURITY LOG'
  if (f.includes('evidence_inventory')) return 'EVIDENCE INVENTORY'
  if (f.includes('receipt')) return 'RECEIPT'
  if (f.includes('restaurant') || f.includes('confirmation')) return 'CONFIRMATION'
  return 'DOCUMENT'
}

/** Generate a stable case ID from current timestamp */
export function generateCaseId(): string {
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `CASE-${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-${Math.random().toString(36).slice(2, 6).toUpperCase()}`
}

/** Truncate a string with ellipsis */
export function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str
  return str.slice(0, maxLen - 3) + '...'
}

/** Format a timestamp string for display */
export function fmtTimestamp(ts: string): string {
  // Handle various formats: ISO, "8:17 PM", "20:15", etc.
  try {
    const d = new Date(ts)
    if (!isNaN(d.getTime())) {
      return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
    }
  } catch {
    // ignore
  }
  return ts
}
