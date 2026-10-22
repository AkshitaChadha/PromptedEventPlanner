import React from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

function App() {
  return (
    <main className="welcome">
      <p className="eyebrow">YOUR CELEBRATION, THOUGHTFULLY PLANNED</p>
      <h1>Make room for the moment.</h1>
      <p className="intro">
        CelebrAI will help you shape a celebration around your people, priorities, and budget.
      </p>
      <p className="status">Project setup is ready. Event planning features are coming next.</p>
    </main>
  )
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
