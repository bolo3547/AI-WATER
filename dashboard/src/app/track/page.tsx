import { redirect } from 'next/navigation'

// Redirect /track to /ticket (the new ticket tracking page with chat)
export default function TrackPage() {
  redirect('/ticket')
}
