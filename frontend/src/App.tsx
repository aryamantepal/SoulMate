import { useCallback, useEffect, useMemo, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import './App.css'
import { supabase } from './supabase'

type TasteVec = Record<string, number>

type Shoe = {
  id: string
  name: string
  brand: string
  v: TasteVec
  image_url: string | null
  url: string | null
  notes: string | null
  match_pct: number
}

type FeedResponse = {
  items: Shoe[]
  taste: TasteVec
  swipe_count: number
}

type SwipeResponse = {
  taste: TasteVec
  swipe_count: number
}

type LoadState = 'loading' | 'ready' | 'error'

const apiBase = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [authReady, setAuthReady] = useState(false)
  const [email, setEmail] = useState('')
  const [authMessage, setAuthMessage] = useState<string | null>(null)
  const [items, setItems] = useState<Shoe[]>([])
  const [taste, setTaste] = useState<TasteVec>({})
  const [swipeCount, setSwipeCount] = useState(0)
  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [error, setError] = useState<string | null>(null)
  const [dragStart, setDragStart] = useState<number | null>(null)

  const activeShoe = items[0]
  const nextShoes = items.slice(1, 3)
  const authToken = session?.access_token ?? null

  const request = useCallback(
    async <T,>(path: string, options: RequestInit = {}): Promise<T> => {
      if (!authToken) {
        throw new Error('Sign in to call protected API routes.')
      }

      const response = await fetch(`${apiBase}${path}`, {
        ...options,
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
          ...options.headers,
        },
      })

      if (!response.ok) {
        const text = await response.text().catch(() => '')
        throw new Error(`API ${response.status}${text ? `: ${text}` : ''}`)
      }

      return response.json() as Promise<T>
    },
    [authToken],
  )

  const loadFeed = useCallback(async () => {
    if (!authReady || !authToken) {
      return
    }

    setLoadState('loading')
    setError(null)

    try {
      const feed = await request<FeedResponse>('/api/feed')
      setItems(feed.items)
      setTaste(feed.taste)
      setSwipeCount(feed.swipe_count)
      setLoadState('ready')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load feed.')
      setLoadState('error')
    }
  }, [authReady, authToken, request])

  const sendMagicLink = useCallback(async () => {
    if (!supabase || !email) {
      return
    }

    setAuthMessage(null)
    const { error: signInError } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: window.location.origin,
      },
    })

    setAuthMessage(
      signInError ? signInError.message : 'Check your email for the SoleMate login link.',
    )
  }, [email])

  const signOut = useCallback(async () => {
    if (!supabase) {
      return
    }

    await supabase.auth.signOut()
    setItems([])
    setTaste({})
    setSwipeCount(0)
  }, [])

  const swipe = useCallback(
    async (direction: 1 | -1) => {
      if (!activeShoe) {
        return
      }

      const swipedId = activeShoe.id
      setItems((current) => current.filter((shoe) => shoe.id !== swipedId))

      try {
        const result = await request<SwipeResponse>('/api/swipe', {
          method: 'POST',
          body: JSON.stringify({ shoe_id: swipedId, direction }),
        })

        setTaste(result.taste)
        setSwipeCount(result.swipe_count)
        await loadFeed()
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to record swipe.')
        await loadFeed()
      }
    },
    [activeShoe, loadFeed, request],
  )

  useEffect(() => {
    if (!authReady || !authToken) {
      return
    }

    const timer = window.setTimeout(() => void loadFeed(), 0)
    return () => window.clearTimeout(timer)
  }, [authReady, authToken, loadFeed])

  useEffect(() => {
    if (!supabase) {
      setAuthReady(true)
      return
    }

    let isMounted = true
    void supabase.auth.getSession().then(({ data }) => {
      if (!isMounted) {
        return
      }

      setSession(data.session)
      setAuthReady(true)
    })

    const { data } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession)
      setAuthReady(true)
    })

    return () => {
      isMounted = false
      data.subscription.unsubscribe()
    }
  }, [])

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'ArrowLeft') {
        void swipe(-1)
      }

      if (event.key === 'ArrowRight') {
        void swipe(1)
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [swipe])

  const sortedTaste = useMemo(
    () => Object.entries(taste).sort(([left], [right]) => left.localeCompare(right)),
    [taste],
  )

  function finishDrag(endX: number) {
    if (dragStart === null) {
      return
    }

    const delta = endX - dragStart
    setDragStart(null)

    if (Math.abs(delta) < 80) {
      return
    }

    void swipe(delta > 0 ? 1 : -1)
  }

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">SoleMate</p>
        <h1>Find the pair that feels weirdly made for you.</h1>
        <p className="lede">
          Swipe right for want, left for pass. The backend updates your taste vector
          and sends back a sharper feed.
        </p>
      </section>

      {!supabase && (
        <section className="auth-card">
          <div>
            <p className="label">Setup</p>
            <h2>Supabase isn't configured.</h2>
            <p>
              Add <code>VITE_SUPABASE_URL</code> and <code>VITE_SUPABASE_ANON_KEY</code> to{' '}
              <code>frontend/.env.local</code>, then restart <code>npm run dev</code>.
            </p>
          </div>
        </section>
      )}

      {supabase && !session && (
        <section className="auth-card">
          <div>
            <p className="label">Supabase auth</p>
            <h2>Sign in to save your taste.</h2>
            <p>Magic-link auth; the backend asks Supabase to verify your token.</p>
          </div>
          <form
            className="auth-form"
            onSubmit={(event) => {
              event.preventDefault()
              void sendMagicLink()
            }}
          >
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              required
            />
            <button type="submit">Send magic link</button>
          </form>
          {authMessage && <p className="panel-note">{authMessage}</p>}
        </section>
      )}

      {supabase && session && (
        <>
          <section className="session-card">
            <span>Signed in as {session.user.email}</span>
            <button type="button" onClick={() => void signOut()}>
              Sign out
            </button>
          </section>

          <section className="app-grid">
            <div className="deck" aria-live="polite">
              {loadState === 'loading' && <div className="empty-card">Loading feed...</div>}
              {loadState === 'error' && (
                <div className="empty-card">
                  <h2>Couldn't load feed</h2>
                  <p>{error}</p>
                </div>
              )}
              {loadState === 'ready' && !activeShoe && (
                <div className="empty-card">
                  <h2>You saw every seed shoe.</h2>
                  <p>Your taste vector and saved shoes still persist across sessions.</p>
                </div>
              )}

              {nextShoes.map((shoe, index) => (
                <article
                  className="shoe-card shoe-card--behind"
                  key={shoe.id}
                  style={{ transform: `translateY(${(index + 1) * 18}px) scale(${0.96 - index * 0.03})` }}
                >
                  <ShoeSummary shoe={shoe} />
                </article>
              ))}

              {activeShoe && (
                <article
                  className="shoe-card shoe-card--active"
                  onPointerDown={(event) => setDragStart(event.clientX)}
                  onPointerCancel={() => setDragStart(null)}
                  onPointerUp={(event) => finishDrag(event.clientX)}
                >
                  <ShoeSummary shoe={activeShoe} />
                  <div className="swipe-actions">
                    <button type="button" onClick={() => void swipe(-1)}>
                      Pass
                    </button>
                    <button type="button" className="want-button" onClick={() => void swipe(1)}>
                      Want
                    </button>
                  </div>
                  <p className="hint">Drag, use arrow keys, or tap a button.</p>
                </article>
              )}
            </div>

            <aside className="taste-panel">
              <p className="label">Taste model</p>
              <h2>{swipeCount} swipes learned</h2>
              <div className="taste-bars">
                {sortedTaste.map(([dim, value]) => (
                  <div className="taste-row" key={dim}>
                    <span>{dim}</span>
                    <div className="bar" aria-label={`${dim}: ${value.toFixed(2)}`}>
                      <div
                        className="bar-fill"
                        style={{
                          width: `${Math.min(Math.abs(value), 1) * 100}%`,
                          marginLeft: value < 0 ? 'auto' : undefined,
                        }}
                      />
                    </div>
                    <strong>{value.toFixed(2)}</strong>
                  </div>
                ))}
              </div>
              <p className="panel-note">
                Match scores are cosine similarity mapped to 0-100 by the FastAPI model.
              </p>
            </aside>
          </section>
        </>
      )}
    </main>
  )
}

function ShoeSummary({ shoe }: { shoe: Shoe }) {
  return (
    <>
      <div className="match-pill">{shoe.match_pct}% match</div>
      <div className="shoe-art" aria-hidden="true">
        {shoe.brand.slice(0, 2)}
      </div>
      <div>
        <p className="label">{shoe.brand}</p>
        <h2>{shoe.name}</h2>
        {shoe.notes && <p>{shoe.notes}</p>}
      </div>
      <div className="dim-tags">
        {Object.entries(shoe.v)
          .sort(([, left], [, right]) => right - left)
          .slice(0, 3)
          .map(([dim, value]) => (
            <span key={dim}>
              {dim} {Math.round(value * 100)}
            </span>
          ))}
      </div>
    </>
  )
}

export default App
