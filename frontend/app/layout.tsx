import type { Metadata } from 'next'
import Link from 'next/link'
import './globals.css'

export const metadata: Metadata = {
  title: 'Job Search Buddy',
  description: 'Daily job matches and skill analysis',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ background: 'var(--bg-dark)', color: 'var(--text-primary)' }} suppressHydrationWarning>

        {/* Nav */}
        <nav style={{
          background: 'rgba(14,14,14,0.95)',
          borderBottom: '1px solid var(--border)',
          padding: '0 20px',
          height: '52px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}>
          <span style={{
            fontFamily: 'Georgia, serif',
            fontStyle: 'italic',
            fontSize: '15px',
            color: 'var(--cream)',
          }}>
            Job Search <span style={{ color: 'var(--yellow)', fontStyle: 'normal' }}>Buddy</span>
          </span>

          <div style={{ display: 'flex', gap: '4px' }}>
            {[
              { href: '/jobs',   label: 'Jobs'   },
              { href: '/skills', label: 'Skills' },
            ].map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                style={{
                  fontFamily: 'DM Mono, monospace',
                  fontSize: '11px',
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase' as const,
                  padding: '6px 14px',
                  borderRadius: '4px',
                  color: 'var(--text-secondary)',
                  textDecoration: 'none',
                  transition: 'color 0.2s',
                }}
              >
                {label}
              </Link>
            ))}
          </div>

          <span
            suppressHydrationWarning
            style={{
              fontFamily: 'DM Mono, monospace',
              fontSize: '10px',
              color: 'var(--text-muted)',
              letterSpacing: '0.1em',
              textTransform: 'uppercase' as const,
            }}
          >
            {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </span>
        </nav>

        <main style={{ maxWidth: '860px', margin: '0 auto', padding: '20px' }}>
          {children}
        </main>

      </body>
    </html>
  )
}
