import { useEffect, useState } from 'react'
import { api, type Health } from './lib/api'

// defining the status type
// usig typescript union to define the three possible states of the application
type Status =
  | { kind: 'checking' } // first state - checking whether the backend is reachable
  | { kind: 'up'; health: Health } // second state - backend respond successfully, stores the health info returned by the backend
  | { kind: 'down' } // third state - application couldn't complete the api request 

// app component 
export default function App() {
  // manage the status with useState
  const [status, setStatus] = useState<Status>({
    kind: 'checking',
  })

  // check the backend when the component first loads
  useEffect(() => {
    async function checkApi() {
      try {
        const health = await api.health()

        setStatus({
          kind: 'up',
          health: health,
        })
      } catch (error) {
          console.error('Health check failed:', error)
          setStatus({ kind: 'down' })
      }
    }

    checkApi()
  }, [])

  // returning the UI
  return (
    <main className="shell">
      <p className="eyebrow">ClearWave</p>

      <h1>Your samples, cleared and paid.</h1>

      <p className="lede">
        Upload a sample, find the released songs that use it,
        reach the people behind them and send a proposal with a
        payment link attached.
      </p>

      <p
        className="status"
        role="status"
        data-kind={status.kind}
      >
        {getStatusMessage(status)}
      </p>
    </main>
  )
}

// function to determines which message to display
function getStatusMessage(status: Status): string {
  if (status.kind === 'checking') {
    return 'Checking the API…'
  }

  if (status.kind === 'down') {
    return 'Can’t reach the API. Is it running on port 8000?'
  }

  if (status.health.database) {
    return 'API and database are up.'
  }

  return 'API is up, but it can’t reach the database.'
}