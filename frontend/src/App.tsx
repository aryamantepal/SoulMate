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

type Deal = {
  shoe_id: string
  name: string
  brand: string
  image_url: string | null
  url: string | null
  lowest_ask: number | null
  retail_price: number | null
  highest_bid: number | null
  price_drop: boolean
  savings?: number
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
  const [password, setPassword] = useState('')
  const [authMode, setAuthMode] = useState<'signIn' | 'signUp'>('signIn')
  const [authMessage, setAuthMessage] = useState<string | null>(null)
  const [items, setItems] = useState<Shoe[]>([])
  const [taste, setTaste] = useState<TasteVec>({})
  const [swipeCount, setSwipeCount] = useState(0)
  const [loadState, setLoadState] = useState<LoadState>('loading')
  const [error, setError] = useState<string | null>(null)
  const [dragStart, setDragStart] = useState<number | null>(null)
  const [deals, setDeals] = useState<Deal[]>([])
  const [dealsOpen, setDealsOpen] = useState(false)

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

  const loadFeed = useCallback(async (silent = false) => {
    if (!authReady || !authToken) {
      return
    }

    if (!silent) {
      setLoadState('loading')
    }
    setError(null)

    try {
      const feed = await request<FeedResponse>('/api/feed')
      setItems(feed.items)
      setTaste(feed.taste)
      setSwipeCount(feed.swipe_count)
      setLoadState('ready')
    } catch (err) {
      if (!silent) {
        setError(err instanceof Error ? err.message : 'Unable to load feed.')
        setLoadState('error')
      }
    }
  }, [authReady, authToken, request])

  const handleAuth = useCallback(async () => {
    if (!supabase || !email || !password) {
      return
    }

    setAuthMessage(null)
    setError(null)

    if (authMode === 'signIn') {
      const { error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      })
      if (signInError) {
        setAuthMessage(signInError.message)
      } else {
        setAuthMessage('Logged in successfully!')
      }
    } else {
      const { error: signUpError } = await supabase.auth.signUp({
        email,
        password,
      })
      if (signUpError) {
        setAuthMessage(signUpError.message)
      } else {
        setAuthMessage('Registration successful! You can now sign in with your password.')
      }
    }
  }, [authMode, email, password])

  const loadDeals = useCallback(async () => {
    try {
      const data = await request<{ items: Deal[] }>('/api/deals')
      setDeals(data.items)
    } catch {
      // Non-fatal — deals panel stays empty
    }
  }, [request])

  const signOut = useCallback(async () => {
    if (!supabase) {
      return
    }

    await supabase.auth.signOut()
    setItems([])
    setTaste({})
    setSwipeCount(0)
    setDeals([])
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
        await loadFeed(true)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to record swipe.')
        await loadFeed(true)
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
          <div className="auth-header">
            <p className="label">Supabase auth</p>
            <h2>{authMode === 'signIn' ? 'Sign in to save your taste' : 'Create an account'}</h2>
            <p className="hint">
              {authMode === 'signIn'
                ? 'Enter your email and password to access your feed.'
                : 'Sign up to start tracking your sneaker preferences.'}
            </p>
          </div>

          <div className="auth-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={authMode === 'signIn'}
              className={`auth-tab ${authMode === 'signIn' ? 'auth-tab--active' : ''}`}
              onClick={() => {
                setAuthMode('signIn')
                setAuthMessage(null)
              }}
            >
              Sign In
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={authMode === 'signUp'}
              className={`auth-tab ${authMode === 'signUp' ? 'auth-tab--active' : ''}`}
              onClick={() => {
                setAuthMode('signUp')
                setAuthMessage(null)
              }}
            >
              Sign Up
            </button>
          </div>

          <form
            className="auth-form-credential"
            onSubmit={(event) => {
              event.preventDefault()
              void handleAuth()
            }}
          >
            <div className="form-group">
              <label htmlFor="auth-email">Email Address</label>
              <input
                id="auth-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="auth-password">Password</label>
              <input
                id="auth-password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="••••••••"
                required
                minLength={6}
              />
            </div>
            <button type="submit" className="want-button auth-submit-btn">
              {authMode === 'signIn' ? 'Sign In' : 'Sign Up'}
            </button>
          </form>
          {authMessage && (
            <p
              className={`panel-note ${
                authMessage.includes('successful') || authMessage.includes('Logged')
                  ? 'success-text'
                  : 'error-text'
              }`}
            >
              {authMessage}
            </p>
          )}
        </section>
      )}

      {supabase && session && (
        <>
          <section className="session-card">
            <span>Signed in as {session.user.email}</span>
            <div className="session-actions">
              <button
                type="button"
                className="deals-button"
                onClick={() => {
                  setDealsOpen((o) => !o)
                  if (!dealsOpen) void loadDeals()
                }}
              >
                {dealsOpen ? 'Hide deals' : 'Price drops'}
              </button>
              <button type="button" onClick={() => void signOut()}>
                Sign out
              </button>
            </div>
          </section>

          {dealsOpen && (
            <section className="deals-panel">
              <p className="label">Price drops on your saved shoes</p>
              {deals.length === 0 ? (
                <p className="hint">No price data yet — save some shoes first.</p>
              ) : (
                <div className="deals-list">
                  {deals.map((deal) => (
                    <div key={deal.shoe_id} className={`deal-row${deal.price_drop ? ' deal-row--drop' : ''}`}>
                      <div className="deal-info">
                        <strong>{deal.name}</strong>
                        <span className="deal-brand">{deal.brand}</span>
                      </div>
                      <div className="deal-prices">
                        {deal.lowest_ask != null && (
                          <span className="deal-ask">${deal.lowest_ask}</span>
                        )}
                        {deal.retail_price != null && (
                          <span className="deal-retail">retail ${deal.retail_price}</span>
                        )}
                        {deal.price_drop && deal.savings != null && (
                          <span className="deal-savings">−${deal.savings} off</span>
                        )}
                      </div>
                      {deal.url && (
                        <a href={deal.url} target="_blank" rel="noopener noreferrer" className="deal-link">
                          View →
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

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
                  <ShoeSummary shoe={activeShoe} taste={taste} />
                  <div
                    className="swipe-actions"
                    onPointerDown={(event) => event.stopPropagation()}
                    onPointerUp={(event) => event.stopPropagation()}
                  >
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

function whyDims(shoe: Shoe, taste: TasteVec): string[] {
  const hasTaste = Object.values(taste).some((v) => Math.abs(v) > 0.01)
  if (!hasTaste) return []
  return Object.entries(shoe.v)
    .map(([dim, shoeVal]) => ({ dim, score: shoeVal * Math.max(0, taste[dim] ?? 0) }))
    .filter(({ score }) => score > 0.1)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)
    .map(({ dim }) => dim)
}

function ShoeSummary({ shoe, taste }: { shoe: Shoe; taste?: TasteVec }) {
  const matchingDims = taste ? whyDims(shoe, taste) : []

  return (
    <>
      <div className="match-pill">{shoe.match_pct}% match</div>
      <div className="shoe-art" aria-hidden="true">
        {shoe.image_url ? (
          <img
            src={shoe.image_url}
            alt={shoe.name}
            loading="lazy"
            referrerPolicy="no-referrer"
          />
        ) : (
          <span>{shoe.brand.slice(0, 2)}</span>
        )}
      </div>
      <div>
        <p className="label">{shoe.brand}</p>
        <h2>{shoe.name}</h2>
        {shoe.notes && <p>{shoe.notes}</p>}
      </div>
      {matchingDims.length > 0 && (
        <div className="why-row">
          <span className="why-label">Why this?</span>
          {matchingDims.map((dim) => (
            <span key={dim} className="why-tag">{dim}</span>
          ))}
        </div>
      )}
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
