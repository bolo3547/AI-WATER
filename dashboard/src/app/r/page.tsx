import { redirect } from 'next/navigation'

// Shortcut URL: /r redirects to /report
export default function QuickReportRedirect() {
  redirect('/report')
}
