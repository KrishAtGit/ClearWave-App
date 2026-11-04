import { useEffect, useState } from "react"
import SignIn from "./components/SignIn"
import { ApiError, api , type User } from "./lib/api"

type Auth = {kind:'loading'} 
          | {kind : 'signed-out'} 
          | {kind: 'signed-in' ; user: User}

function takeExpiredFlag(): boolean {
  const params = new URLSearchParams(window.location.search)
  const expired = params.get('signin') === 'expired'
  if(expired){
    window.history.replaceState(null, '', window.location.pathname)
  }
  return expired
}

export default function App(){
  const [auth, setAuth] = useState<Auth>(
    {kind:'loading'}
  )
  const [linkExpired] = useState(takeExpiredFlag)

  useEffect(() => {
    api
      .me()
      .then((user) => setAuth({kind: 'signed-in', user}))
      .catch((error) => {
        if(!(error instanceof ApiError && error.status === 401)) {
          console.error('Checking the session failed: ', error)
        }
        setAuth({kind: 'signed-out'})
      })
    }, [])
    
    async function signOut(){
      await api.logout()
      setAuth({kind:'signed-out'})
    }

    return (
      <main className="shell">
        <header className="top">
          <p className="eyebrow">
            ClearWave
          </p>
          {auth.kind === 'signed-in' && (
            <div className="account">
              <span>{auth.user.email}</span>
              <button type="button" className="link" onClick={signOut}>
                Sign Out
              </button>
            </div>
          )}

        </header>

        <h1>Your Samples, cleared and paid.</h1>

        {auth.kind === 'loading' && <p className="hint">Loading...</p>}
        {auth.kind === 'signed-out' && (
          <>
          <p className="lede">
            Uplod a sample, find the released songs that use it, reach the people behind them and send a proposal with a payment link attached.
          </p>
          <SignIn linkExpired={linkExpired}/>
          </>
        )}
      </main>
    )
}