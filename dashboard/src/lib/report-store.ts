// Shared in-memory report store for when MongoDB is unavailable
// Uses globalThis to ensure the same Map instance is shared across all API route bundles

interface PublicReport {
  id: string
  ticket: string
  ticket_number: string
  tenant_id: string
  category: string
  description: string | null
  latitude: number | null
  longitude: number | null
  area_text: string | null
  source: string
  severity: string
  reporter_name: string | null
  reporter_phone: string | null
  reporter_email: string | null
  reporter_consent: boolean
  status: string
  verification: string
  spam_flag: boolean
  quarantine: boolean
  created_at: string
  updated_at: string
  timeline: { status: string; message: string; timestamp: string; updated_by?: string }[]
}

// Use globalThis to share the Map across all API route bundles
const globalWithReports = globalThis as typeof globalThis & {
  _inMemoryReports?: Map<string, PublicReport>
}

if (!globalWithReports._inMemoryReports) {
  globalWithReports._inMemoryReports = new Map<string, PublicReport>()
}

const inMemoryReports: Map<string, PublicReport> = globalWithReports._inMemoryReports

// Try to get MongoDB collection, return null if unavailable
async function getMongoCollection() {
  try {
    const { default: clientPromise } = await import('@/lib/mongodb')
    const client = await clientPromise
    const db = client.db('lwsc')
    return db.collection('public_reports')
  } catch (error) {
    console.log('[ReportStore] MongoDB unavailable, using in-memory store:', (error as Error).message)
    return null
  }
}

export { inMemoryReports, getMongoCollection }
export type { PublicReport }
