import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
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

type SwipeRecord = {
  shoe_id: string
  direction: 1 | -1
  shoe: Shoe
  created_at: string
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
  has_market_data: boolean
  savings?: number
  matched_name?: string
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

function proxyImg(url: string | null): string | null {
  if (!url) return null
  // Local paths (seed shoe assets) are served directly by the frontend CDN
  if (url.startsWith('/')) return url
  return `${apiBase}/api/img?url=${encodeURIComponent(url)}`
}

function ShoeImage({ url, name, brand }: { url: string | null; name: string; brand: string }) {
  const initials = brand.slice(0, 2).toUpperCase()
  if (!url) return <span>{initials}</span>
  return (
    <img
      src={url}
      alt={name}
      loading="lazy"
      referrerPolicy="no-referrer"
      onError={(e) => {
        const el = e.currentTarget
        el.style.display = 'none'
        const parent = el.parentElement
        if (parent && !parent.querySelector('span')) {
          const span = document.createElement('span')
          span.textContent = initials
          parent.appendChild(span)
        }
      }}
    />
  )
}

// Fire-and-forget ping to wake the backend before the user finishes signing in
fetch(`${apiBase}/api/health`).catch(() => {})

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
  const [slowLoad, setSlowLoad] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragOffset, setDragOffset] = useState(0)
  const [deals, setDeals] = useState<Deal[]>([])
  const [dealsOpen, setDealsOpen] = useState(false)
  const [catalogCount, setCatalogCount] = useState<number | null>(null)
  const [lastSwipe, setLastSwipe] = useState<{ shoe: Shoe; direction: 1 | -1 } | null>(null)
  const [savedShoes, setSavedShoes] = useState<Shoe[]>([])
  const [savedOpen, setSavedOpen] = useState(false)
  const [onboarding, setOnboarding] = useState(false)
  const [history, setHistory] = useState<SwipeRecord[]>([])
  const [historyOpen, setHistoryOpen] = useState(false)
  const [historyFilter, setHistoryFilter] = useState<'all' | 'liked' | 'passed'>('all')
  const [notifyStatus, setNotifyStatus] = useState<'idle' | 'sending' | 'sent'>('idle')
  const [tastePanelOpen, setTastePanelOpen] = useState(false)

  const isSharedPath = window.location.pathname.startsWith('/taste/')
  const shareToken = isSharedPath ? window.location.pathname.split('/').pop() : null

  const [sharedTaste, setSharedTaste] = useState<TasteVec | null>(null)
  const [sharedSwipeCount, setSharedSwipeCount] = useState<number>(0)
  const [sharedLoadState, setSharedLoadState] = useState<LoadState>('loading')
  const [sharedError, setSharedError] = useState<string | null>(null)

  const [shareCopied, setShareCopied] = useState(false)
  const [shareLoading, setShareLoading] = useState(false)

  const [modalShoe, setModalShoe] = useState<Shoe | null>(null)
  const dragStartX = useRef<number | null>(null)
  const isDragging = useRef(false)

  const activeShoe = items[0]
  const nextShoes = items.slice(1, 3)
  const authToken = session?.access_token ?? null

  const request = useCallback(
    async <T,>(path: string, options: RequestInit = {}): Promise<T> => {
      const freshSession = await supabase?.auth.getSession()
      const token = freshSession?.data.session?.access_token ?? authToken
      if (!token) {
        throw new Error('Sign in to call protected API routes.')
      }

      const response = await fetch(`${apiBase}${path}`, {
        ...options,
        headers: {
          Authorization: `Bearer ${token}`,
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

  const loadCatalogCount = useCallback(async () => {
    try {
      const data = await request<{ count: number }>('/api/catalog/count')
      setCatalogCount(data.count)
    } catch { /* non-fatal */ }
  }, [request])

  const loadFeed = useCallback(async (silent = false) => {
    if (!authReady || !authToken) {
      return
    }

    if (!silent) {
      setLoadState('loading')
      setSlowLoad(false)
    }
    setError(null)

    const slowTimer = window.setTimeout(() => setSlowLoad(true), 4000)
    try {
      const feed = await request<FeedResponse>('/api/feed')
      window.clearTimeout(slowTimer)
      setSlowLoad(false)
      setItems(feed.items.map(s => ({ ...s, image_url: proxyImg(s.image_url) })))
      setTaste(feed.taste)
      setSwipeCount(feed.swipe_count)
      setLoadState('ready')
      if (catalogCount === null) void loadCatalogCount()
      if (!silent && feed.swipe_count === 0) setOnboarding(true)
    } catch (err) {
      window.clearTimeout(slowTimer)
      setSlowLoad(false)
      if (!silent) {
        setError(err instanceof Error ? err.message : 'Unable to load feed.')
        setLoadState('error')
      }
    }
  }, [authReady, authToken, request, catalogCount, loadCatalogCount])

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

  const resetTaste = useCallback(async () => {
    try {
      await request('/api/taste', { method: 'DELETE' })
      await request('/api/seen', { method: 'DELETE' })
      setTaste({})
      setSwipeCount(0)
      setItems([])
      setLastSwipe(null)
      setOnboarding(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to reset taste.')
    }
  }, [request])

  const onboardingSwipe = useCallback(async (archetypeId: string, direction: 1 | -1) => {
    // Use the archetype id as a synthetic shoe_id; backend needs a real shoe id,
    // so we map to the closest seed shoe id by dimension similarity instead.
    // Simpler approach: just send a taste nudge by posting swipes against
    // the archetype seed ids we have in the catalog.
    const archetypeShoeMap: Record<string, string> = {
      'retro-earthy':    'clarks-wallabee-maple-suede',
      'techy-gorpcore':  'salomon-xt-6-safari',
      'clean-minimal':   'maison-margiela-replica-gat-cream',
      'bold-statement':  'puma-palermo-vine-clementine',
      'chunky-dad':      'new-balance-9060-sea-salt',
    }
    const shoeId = archetypeShoeMap[archetypeId]
    if (!shoeId) return
    try {
      const result = await request<SwipeResponse>('/api/swipe', {
        method: 'POST',
        body: JSON.stringify({ shoe_id: shoeId, direction }),
      })
      setTaste(result.taste)
      setSwipeCount(result.swipe_count)
    } catch { /* best-effort */ }
  }, [request])

  const resetSeen = useCallback(async () => {
    try {
      setLoadState('loading')
      setItems([])
      await request('/api/seen', { method: 'DELETE' })
      await loadFeed()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to reset feed.')
      setLoadState('error')
    }
  }, [request, loadFeed])

  const loadHistory = useCallback(async (filter: 'all' | 'liked' | 'passed') => {
    const dirParam = filter === 'liked' ? '?direction=1' : filter === 'passed' ? '?direction=-1' : ''
    try {
      const data = await request<{ items: SwipeRecord[] }>(`/api/swipes${dirParam}`)
      const items = data.items ?? []
      // Auto-backfill: if history is empty but we have saved shoes, recover liked swipes
      if (items.length === 0 && filter === 'all') {
        try {
          await request<{ inserted: number }>('/api/swipes/backfill', { method: 'POST' })
          const retry = await request<{ items: SwipeRecord[] }>('/api/swipes')
          setHistory((retry.items ?? []).map(r => ({ ...r, shoe: { ...r.shoe, image_url: proxyImg(r.shoe.image_url) } })))
          return
        } catch { /* backfill is best-effort */ }
      }
      setHistory(items.map(r => ({ ...r, shoe: { ...r.shoe, image_url: proxyImg(r.shoe.image_url) } })))
    } catch (err) {
      setHistory([])
      console.error('History load failed:', err)
    }
  }, [request])

  const loadSaved = useCallback(async () => {
    try {
      const data = await request<{ items: Shoe[] }>('/api/saved')
      setSavedShoes(data.items.map(s => ({ ...s, image_url: proxyImg(s.image_url) })))
    } catch { /* non-fatal */ }
  }, [request])

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
    setSavedShoes([])
    setSavedOpen(false)
  }, [])

  const swipe = useCallback(
    async (direction: 1 | -1) => {
      if (!activeShoe) {
        return
      }

      const swipedShoe = activeShoe
      setItems((current) => current.filter((shoe) => shoe.id !== swipedShoe.id))
      setLastSwipe({ shoe: swipedShoe, direction })

      try {
        const result = await request<SwipeResponse>('/api/swipe', {
          method: 'POST',
          body: JSON.stringify({ shoe_id: swipedShoe.id, direction }),
        })

        setTaste(result.taste)
        setSwipeCount(result.swipe_count)
        // Only refill when deck is almost empty to avoid replacing items mid-swipe
        setItems((current) => {
          if (current.length < 2) void loadFeed(true)
          return current
        })
        if (direction === 1) void loadSaved()
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to record swipe.')
      }
    },
    [activeShoe, loadFeed, loadSaved, request],
  )

  const undo = useCallback(async () => {
    if (!lastSwipe) return
    const { shoe, direction } = lastSwipe
    setLastSwipe(null)
    // Put shoe back at front of deck
    setItems((current) => [shoe, ...current])
    // Fire compensating swipe to reverse taste update
    try {
      const result = await request<SwipeResponse>('/api/swipe', {
        method: 'POST',
        body: JSON.stringify({ shoe_id: shoe.id, direction: -direction as 1 | -1 }),
      })
      setTaste(result.taste)
      setSwipeCount(result.swipe_count)
    } catch { /* best-effort */ }
  }, [lastSwipe, request])

  const shareTasteProfile = useCallback(async () => {
    if (shareLoading) return
    setShareLoading(true)
    try {
      const data = await request<{ share_token: string }>('/api/taste/share')
      const shareUrl = `${window.location.origin}/taste/${data.share_token}`
      await navigator.clipboard.writeText(shareUrl)
      setShareCopied(true)
      setTimeout(() => setShareCopied(false), 3000)
    } catch (err) {
      console.error('Failed to share taste profile:', err)
      alert('Unable to copy share link. Please try again.')
    } finally {
      setShareLoading(false)
    }
  }, [request, shareLoading])

  useEffect(() => {
    if (!isSharedPath || !shareToken) return

    setSharedLoadState('loading')
    setSharedError(null)

    fetch(`${apiBase}/api/taste/public/${shareToken}`)
      .then((res) => {
        if (!res.ok) {
          throw new Error(`Profile not found (status ${res.status})`)
        }
        return res.json()
      })
      .then((data: any) => {
        setSharedTaste(data.taste)
        setSharedSwipeCount(data.swipe_count)
        setSharedLoadState('ready')
      })
      .catch((err) => {
        setSharedError(err instanceof Error ? err.message : 'Failed to load shared profile')
        setSharedLoadState('error')
      })
  }, [isSharedPath, shareToken])

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
      if (event.key === 'ArrowLeft') void swipe(-1)
      if (event.key === 'ArrowRight') void swipe(1)
      if (event.key === 'z' && (event.metaKey || event.ctrlKey)) void undo()
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [swipe, undo])

  const sortedTaste = useMemo(
    () => Object.entries(taste).sort(([left], [right]) => left.localeCompare(right)),
    [taste],
  )

  function handleDragStart(clientX: number) {
    dragStartX.current = clientX
    isDragging.current = false
    setDragOffset(0)
  }

  function handleDragMove(clientX: number) {
    if (dragStartX.current === null) return
    const delta = clientX - dragStartX.current
    if (Math.abs(delta) > 5) isDragging.current = true
    setDragOffset(delta)
  }

  function handleDragEnd(clientX: number) {
    if (dragStartX.current === null) {
      setDragOffset(0)
      return
    }
    const delta = clientX - dragStartX.current
    dragStartX.current = null
    setDragOffset(0)

    if (Math.abs(delta) >= 80) {
      void swipe(delta > 0 ? 1 : -1)
    }
  }

  function handleDragCancel() {
    dragStartX.current = null
    setDragOffset(0)
  }

  if (isSharedPath) {
    const sortedSharedTaste = sharedTaste
      ? Object.entries(sharedTaste).sort(([left], [right]) => left.localeCompare(right))
      : []
    return (
      <main className="shell">
        <section className="hero">
          <p className="eyebrow">SoleMate</p>
          <h1>Sneaker Taste Profile</h1>
          <p className="lede">
            A read-only snapshot of this sneaker lover's preferred styles.
          </p>
        </section>

        <section className="shared-profile-container">
          {sharedLoadState === 'loading' && (
            <div className="empty-card loading-card">
              <div className="spinner-glow" />
              <div className="spinner" />
              <div className="loading-status">
                <p className="loading-title">Loading profile…</p>
              </div>
            </div>
          )}
          {sharedLoadState === 'error' && (
            <div className="empty-card">
              <h2>Failed to load profile</h2>
              <p>{sharedError}</p>
              <button
                type="button"
                className="want-button"
                style={{ marginTop: '16px', padding: '10px 24px', borderRadius: '12px' }}
                onClick={() => { window.location.href = '/' }}
              >
                Go Home
              </button>
            </div>
          )}
          {sharedLoadState === 'ready' && sharedTaste && (
            <div className="shared-taste-layout">
              <div className="taste-panel public-taste-panel">
                <p className="label">Public Profile</p>
                <h2>{sharedSwipeCount} swipes learned</h2>
                <div className="taste-bars">
                  {sortedSharedTaste.map(([dim, value]) => (
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
                <div className="shared-cta-section">
                  <p className="hint">Ready to find the pair that feels weirdly made for you?</p>
                  <button
                    type="button"
                    className="want-button shared-join-btn"
                    onClick={() => { window.location.href = '/' }}
                  >
                    Find Your SoleMate →
                  </button>
                </div>
              </div>
            </div>
          )}
        </section>
      </main>
    )
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

      {supabase && session && onboarding && (
        <OnboardingQuiz
          onSwipe={onboardingSwipe}
          onSkip={() => {
            setOnboarding(false)
            void loadFeed(true)
          }}
        />
      )}

      {supabase && session && (
        <>
          <section className="session-card">
            <span>Signed in as {session.user.email}</span>
            <div className="session-actions">
              <button
                type="button"
                className="saved-button"
                onClick={() => {
                  setSavedOpen((o) => !o)
                  setDealsOpen(false)
                  setHistoryOpen(false)
                  if (!savedOpen) void loadSaved()
                }}
              >
                {savedOpen ? 'Hide saved' : `Saved${savedShoes.length > 0 ? ` (${savedShoes.length})` : ''}`}
              </button>
              <button
                type="button"
                className="history-button"
                onClick={() => {
                  setHistoryOpen((o) => !o)
                  setSavedOpen(false)
                  setDealsOpen(false)
                  if (!historyOpen) void loadHistory(historyFilter)
                }}
              >
                {historyOpen ? 'Hide history' : 'History'}
              </button>
              <button
                type="button"
                className="deals-button"
                onClick={() => {
                  setDealsOpen((o) => !o)
                  setSavedOpen(false)
                  setHistoryOpen(false)
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

          {savedOpen && (
            <section className="saved-panel">
              <p className="label">Your saved shoes</p>
              {savedShoes.length === 0 ? (
                <div className="empty-state">
                  <span className="empty-state-icon">👟</span>
                  <p className="empty-state-text">Nothing saved yet</p>
                  <p className="hint">Swipe right on shoes in the feed to save them here.</p>
                </div>
              ) : (
                <div className="saved-grid">
                  {savedShoes.map((shoe) => (
                    <div key={shoe.id} className="saved-card">
                      <div className="saved-art">
                        <ShoeImage url={shoe.image_url} name={shoe.name} brand={shoe.brand} />
                      </div>
                      <div className="saved-info">
                        <span className="saved-brand">{shoe.brand}</span>
                        <strong>{shoe.name}</strong>
                        {shoe.notes && <span className="saved-notes">{shoe.notes}</span>}
                        <span className="saved-match">{shoe.match_pct}% match</span>
                      </div>
                      {shoe.url && (
                        <a href={shoe.url} target="_blank" rel="noopener noreferrer" className="deal-link">
                          View →
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {historyOpen && (
            <section className="saved-panel">
              <div className="history-header">
                <p className="label">Swipe history</p>
                <div className="history-filters">
                  {(['all', 'liked', 'passed'] as const).map((f) => (
                    <button
                      key={f}
                      type="button"
                      className={`history-filter${historyFilter === f ? ' history-filter--active' : ''}`}
                      onClick={() => {
                        setHistoryFilter(f)
                        void loadHistory(f)
                      }}
                    >
                      {f === 'all' ? 'All' : f === 'liked' ? '✓ Liked' : '✗ Passed'}
                    </button>
                  ))}
                </div>
              </div>
              {history.length === 0 ? (
                <div className="empty-state">
                  <span className="empty-state-icon">
                    {historyFilter === 'liked' ? '✓' : historyFilter === 'passed' ? '✗' : '⏳'}
                  </span>
                  <p className="empty-state-text">
                    {historyFilter === 'all'
                      ? 'No swipes yet'
                      : historyFilter === 'liked'
                      ? 'No liked shoes yet'
                      : 'No passed shoes yet'}
                  </p>
                  <p className="hint">
                    {historyFilter === 'all'
                      ? 'Your swiped shoes will appear here.'
                      : historyFilter === 'liked'
                      ? 'Swipe right on shoes to like them.'
                      : 'Swipe left on shoes to pass on them.'}
                  </p>
                </div>
              ) : (
                <div className="saved-grid">
                  {history.map((record) => (
                    <div
                      key={`${record.shoe_id}-${record.created_at}`}
                      className={`saved-card history-card${record.direction === 1 ? ' history-card--liked' : ' history-card--passed'}`}
                    >
                      <div className="saved-art">
                        <ShoeImage url={record.shoe.image_url} name={record.shoe.name} brand={record.shoe.brand} />
                      </div>
                      <div className="saved-info">
                        <span className="saved-brand">{record.shoe.brand}</span>
                        <strong>{record.shoe.name}</strong>
                        <span className={`history-badge${record.direction === 1 ? ' history-badge--liked' : ' history-badge--passed'}`}>
                          {record.direction === 1 ? '✓ Liked' : '✗ Passed'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {dealsOpen && (
            <section className="deals-panel">
              <p className="label">Market prices for your saved shoes</p>
              {deals.some((d) => d.price_drop) && (
                <div style={{ marginBottom: '12px' }}>
                  <button
                    type="button"
                    className="want-button"
                    style={{ fontSize: '0.8rem', padding: '6px 14px' }}
                    disabled={notifyStatus === 'sending'}
                    onClick={async () => {
                      setNotifyStatus('sending')
                      try {
                        await request('/api/deals/notify', { method: 'POST' })
                        setNotifyStatus('sent')
                        setTimeout(() => setNotifyStatus('idle'), 3000)
                      } catch {
                        setNotifyStatus('idle')
                      }
                    }}
                  >
                    {notifyStatus === 'sent' ? 'Email sent!' : notifyStatus === 'sending' ? 'Sending…' : 'Email me these drops'}
                  </button>
                </div>
              )}
              {deals.length === 0 ? (
                <div className="empty-state">
                  <span className="empty-state-icon">📉</span>
                  <p className="empty-state-text">No deals monitored yet</p>
                  <p className="hint">Save shoes first to monitor price drops and market values.</p>
                </div>
              ) : (
                <div className="deals-list">
                  {deals.map((deal) => (
                    <div key={deal.shoe_id} className={`deal-row${deal.price_drop ? ' deal-row--drop' : ''}`}>
                      <div className="deal-info">
                        <strong>{deal.name}</strong>
                        <span className="deal-brand">{deal.brand}</span>
                      </div>
                      <div className="deal-prices">
                        {deal.has_market_data ? (
                          <>
                            {deal.lowest_ask != null && (
                              <span className="deal-ask">${deal.lowest_ask}</span>
                            )}
                            {deal.retail_price != null && (
                              <span className="deal-retail">retail ${deal.retail_price}</span>
                            )}
                            {deal.price_drop && deal.savings != null && (
                              <span className="deal-savings">−${deal.savings} off</span>
                            )}
                          </>
                        ) : (
                          <span className="deal-no-data">No market data</span>
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
              {loadState === 'loading' && (
                <div className="empty-card loading-card">
                  <div className="spinner-glow" />
                  <div className="spinner" />
                  {slowLoad ? (
                    <div className="loading-status">
                      <p className="loading-title">Waking up the server…</p>
                      <p className="loading-subtitle">
                        Free tier cold start, ~30s
                      </p>
                    </div>
                  ) : (
                    <div className="loading-status">
                      <p className="loading-title">Loading feed…</p>
                    </div>
                  )}
                </div>
              )}
              {loadState === 'error' && (
                <div className="empty-card">
                  <h2>Couldn't load feed</h2>
                  <p>{error}</p>
                </div>
              )}
              {loadState === 'ready' && !activeShoe && (
                <div className="empty-card">
                  <h2>You've seen everything.</h2>
                  <p>Your taste vector and saves persist. Shuffle to see the catalog fresh.</p>
                  <button
                    type="button"
                    className="want-button"
                    style={{ marginTop: '16px' }}
                    onClick={() => void resetSeen()}
                  >
                    Shuffle again
                  </button>
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
                  style={dragOffset !== 0 ? {
                    transform: `translateX(${dragOffset}px) rotate(${dragOffset * 0.04}deg)`,
                    transition: 'none',
                  } : undefined}
                  onPointerDown={(e) => handleDragStart(e.clientX)}
                  onPointerMove={(e) => handleDragMove(e.clientX)}
                  onPointerUp={(e) => {
                    if (!isDragging.current) return // let click through
                    handleDragEnd(e.clientX)
                  }}
                  onPointerCancel={handleDragCancel}
                  onTouchStart={(e) => handleDragStart(e.touches[0].clientX)}
                  onTouchMove={(e) => handleDragMove(e.touches[0].clientX)}
                  onTouchEnd={(e) => {
                    const x = e.changedTouches[0]?.clientX
                    if (x !== undefined) handleDragEnd(x)
                  }}
                >
                  <span
                    className={`swipe-hint-label swipe-hint-label--want${dragOffset > 40 ? ' swipe-hint-label--visible' : ''}`}
                  >
                    Want
                  </span>
                  <span
                    className={`swipe-hint-label swipe-hint-label--pass${dragOffset < -40 ? ' swipe-hint-label--visible' : ''}`}
                  >
                    Pass
                  </span>
                  <ShoeSummary shoe={activeShoe} taste={taste} onExpand={() => { if (!isDragging.current) setModalShoe(activeShoe) }} />
                  <div
                    className="swipe-actions"
                    onPointerDown={(event) => event.stopPropagation()}
                    onPointerUp={(event) => event.stopPropagation()}
                    onTouchStart={(event) => event.stopPropagation()}
                  >
                    <button type="button" onClick={() => void swipe(-1)}>
                      Pass
                    </button>
                    <button type="button" className="want-button" onClick={() => void swipe(1)}>
                      Want
                    </button>
                  </div>
                  <div
                    className="card-meta-row"
                    onPointerDown={(e) => e.stopPropagation()}
                    onPointerUp={(e) => e.stopPropagation()}
                    onTouchStart={(e) => e.stopPropagation()}
                  >
                    {lastSwipe && (
                      <button type="button" className="undo-button" onClick={() => void undo()}>
                        ↩ Undo
                      </button>
                    )}
                    <p className="hint">Swipe or tap · ← → keys · ⌘Z undo</p>
                  </div>
                </article>
              )}
            </div>

            <button
              type="button"
              className="taste-panel-toggle"
              onClick={() => setTastePanelOpen((o) => !o)}
            >
              <span>Taste model — {swipeCount} swipes</span>
              <span className={`taste-toggle-chevron${tastePanelOpen ? ' taste-toggle-chevron--open' : ''}`}>▼</span>
            </button>
            <aside className={`taste-panel${!tastePanelOpen ? ' taste-panel--collapsed' : ''}`}>
              <p className="label">Taste model</p>
              <h2>{swipeCount} swipes learned</h2>
              {catalogCount !== null && (
                <p className="catalog-count">{catalogCount} shoes in catalog</p>
              )}
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
              <button
                type="button"
                className="share-taste-button want-button"
                style={{ width: '100%', marginBottom: '12px', marginTop: '16px', borderRadius: '12px', padding: '10px 14px' }}
                onClick={() => void shareTasteProfile()}
                disabled={shareLoading}
              >
                {shareLoading ? 'Generating Link…' : shareCopied ? 'Link Copied! 📋' : 'Share taste profile'}
              </button>
              <button
                type="button"
                className="reset-taste-button"
                onClick={() => { if (window.confirm('Reset your taste profile? This clears your learned preferences and restarts the quiz.')) void resetTaste() }}
              >
                Reset taste profile
              </button>
            </aside>
          </section>
        </>
      )}
      {modalShoe && (
        <ShoeDetailModal
          shoe={modalShoe}
          taste={taste}
          onClose={() => setModalShoe(null)}
        />
      )}
    </main>
  )
}

// ── Onboarding archetypes ────────────────────────────────────────────────────
const ARCHETYPES: { id: string; label: string; desc: string; emoji: string; v: TasteVec }[] = [
  {
    id: 'retro-earthy',
    label: 'Vintage & Earthy',
    desc: 'Suede, gum soles, warm tones. NB 550s, Sambas, Wallabees.',
    emoji: '🟫',
    v: { chunk: 0.3, retro: 0.95, warm: 0.90, minimal: 0.70, earthy: 0.92, loud: 0.15, techy: 0.05 },
  },
  {
    id: 'techy-gorpcore',
    label: 'Techy & Trail',
    desc: 'Gore-Tex, trail lugs, technical palettes. Salomon, Hoka, ACG.',
    emoji: '🟢',
    v: { chunk: 0.70, retro: 0.12, warm: 0.55, minimal: 0.30, earthy: 0.65, loud: 0.45, techy: 0.95 },
  },
  {
    id: 'clean-minimal',
    label: 'Clean & Minimal',
    desc: 'White leather, tonal, nothing extra. AF1s, Common Projects, Killshot.',
    emoji: '⬜',
    v: { chunk: 0.20, retro: 0.65, warm: 0.45, minimal: 0.95, earthy: 0.30, loud: 0.05, techy: 0.08 },
  },
  {
    id: 'bold-statement',
    label: 'Bold & Loud',
    desc: 'Color, energy, presence. AM97, Dunks, collabs that turn heads.',
    emoji: '🔴',
    v: { chunk: 0.55, retro: 0.60, warm: 0.40, minimal: 0.10, earthy: 0.20, loud: 0.95, techy: 0.50 },
  },
  {
    id: 'chunky-dad',
    label: 'Chunky & Maximal',
    desc: 'Big soles, stacked silhouettes. 9060s, Cliftons, Yeezys.',
    emoji: '🏔',
    v: { chunk: 0.95, retro: 0.50, warm: 0.60, minimal: 0.20, earthy: 0.45, loud: 0.40, techy: 0.55 },
  },
]

function OnboardingQuiz({
  onSwipe,
  onSkip,
}: {
  onSwipe: (archetypeId: string, direction: 1 | -1) => Promise<void>
  onSkip: () => void
}) {
  const [step, setStep] = useState(0)
  const [busy, setBusy] = useState(false)
  const current = ARCHETYPES[step]

  async function answer(direction: 1 | -1) {
    if (busy) return
    setBusy(true)
    await onSwipe(current.id, direction)
    setBusy(false)
    if (step < ARCHETYPES.length - 1) {
      setStep((s) => s + 1)
    } else {
      onSkip()
    }
  }

  return (
    <section className="onboarding-overlay">
      <div className="onboarding-card">
        <p className="label">Quick taste quiz · {step + 1} of {ARCHETYPES.length}</p>
        <h2>Which vibe speaks to you?</h2>
        <div className="onboarding-progress">
          {ARCHETYPES.map((_, i) => (
            <div key={i} className={`onboarding-dot${i <= step ? ' onboarding-dot--active' : ''}`} />
          ))}
        </div>
        <div className="onboarding-archetype">
          <span className="onboarding-emoji">{current.emoji}</span>
          <div>
            <strong>{current.label}</strong>
            <p>{current.desc}</p>
          </div>
        </div>
        <div className="onboarding-actions">
          <button type="button" disabled={busy} onClick={() => void answer(-1)}>
            Not me
          </button>
          <button type="button" className="want-button" disabled={busy} onClick={() => void answer(1)}>
            That's me
          </button>
        </div>
        <button type="button" className="onboarding-skip" onClick={onSkip}>
          Skip setup
        </button>
      </div>
    </section>
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

function ShoeSummary({ shoe, taste, onExpand }: { shoe: Shoe; taste?: TasteVec; onExpand?: () => void }) {
  const matchingDims = taste ? whyDims(shoe, taste) : []

  return (
    <>
      <div className="match-pill">{shoe.match_pct}% match</div>
      <div
        className={`shoe-art${onExpand ? ' shoe-art--clickable' : ''}`}
        aria-hidden="true"
        onClick={onExpand}
        onPointerDown={onExpand ? (e) => e.stopPropagation() : undefined}
        onPointerUp={onExpand ? (e) => e.stopPropagation() : undefined}
      >
        <ShoeImage url={shoe.image_url} name={shoe.name} brand={shoe.brand} />
        {onExpand && <span className="shoe-art-expand" aria-label="Expand">⤢</span>}
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

const DIM_ORDER = ['chunk', 'retro', 'warm', 'minimal', 'earthy', 'loud', 'techy']

function ShoeDetailModal({ shoe, taste, onClose }: { shoe: Shoe; taste: TasteVec; onClose: () => void }) {
  const matchingDims = whyDims(shoe, taste)
  const dims = DIM_ORDER.filter((d) => d in shoe.v)
  const [sheetDragY, setSheetDragY] = useState(0)
  const sheetDragStartY = useRef<number | null>(null)

  // Close on Escape key
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  function handleSheetDragStart(clientY: number) {
    sheetDragStartY.current = clientY
  }

  function handleSheetDragMove(clientY: number) {
    if (sheetDragStartY.current === null) return
    const delta = clientY - sheetDragStartY.current
    // Only allow dragging downward
    setSheetDragY(Math.max(0, delta))
  }

  function handleSheetDragEnd() {
    sheetDragStartY.current = null
    if (sheetDragY > 100) {
      onClose()
    }
    setSheetDragY(0)
  }

  return (
    <div
      className="modal-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={`${shoe.brand} ${shoe.name} detail`}
    >
      <div
        className="modal-card"
        onClick={(e) => e.stopPropagation()}
        style={sheetDragY > 0 ? {
          transform: `translateY(${sheetDragY}px)`,
          transition: 'none',
        } : undefined}
      >
        <div
          className="modal-drag-handle"
          onTouchStart={(e) => handleSheetDragStart(e.touches[0].clientY)}
          onTouchMove={(e) => handleSheetDragMove(e.touches[0].clientY)}
          onTouchEnd={handleSheetDragEnd}
          onPointerDown={(e) => handleSheetDragStart(e.clientY)}
          onPointerMove={(e) => { if (sheetDragStartY.current !== null) handleSheetDragMove(e.clientY) }}
          onPointerUp={handleSheetDragEnd}
        />
        <button type="button" className="modal-close" onClick={onClose} aria-label="Close">✕</button>

        <div className="modal-image">
          <ShoeImage url={shoe.image_url} name={shoe.name} brand={shoe.brand} />
        </div>

        <div className="modal-header">
          <p className="label">{shoe.brand}</p>
          <h2 className="modal-title">{shoe.name}</h2>
          {shoe.notes && <p className="modal-notes">{shoe.notes}</p>}
          <div className="match-pill" style={{ marginTop: '8px' }}>{shoe.match_pct}% match</div>
        </div>

        <div className="modal-section">
          <p className="label">Dimension scores</p>
          <div className="modal-bars">
            {dims.map((dim) => {
              const value = shoe.v[dim] ?? 0
              return (
                <div className="taste-row" key={dim}>
                  <span>{dim}</span>
                  <div className="bar" aria-label={`${dim}: ${value.toFixed(2)}`}>
                    <div
                      className="bar-fill"
                      style={{ width: `${Math.min(Math.abs(value), 1) * 100}%` }}
                    />
                  </div>
                  <strong>{value.toFixed(2)}</strong>
                </div>
              )
            })}
          </div>
        </div>

        {matchingDims.length > 0 && (
          <div className="modal-section">
            <p className="label">Why this?</p>
            <div className="why-row" style={{ marginTop: '8px' }}>
              {matchingDims.map((dim) => (
                <span key={dim} className="why-tag">{dim}</span>
              ))}
            </div>
          </div>
        )}

        {shoe.url && (
          <a
            href={shoe.url}
            target="_blank"
            rel="noopener noreferrer"
            className="modal-cta"
          >
            View on StockX / GOAT →
          </a>
        )}
      </div>
    </div>
  )
}

export default App
