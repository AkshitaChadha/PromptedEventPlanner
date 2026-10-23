import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { createEvent, getEvents, setTaskCompletion } from './services/events.js'
import './style.css'

const listFields = [
  ['user_preferences', 'What matters to you?', 'e.g. relaxed, outdoors, family-friendly'],
  ['must_have_arrangements', 'Must-have arrangements', 'e.g. live music, children’s corner'],
  ['things_to_avoid', 'Things to avoid', 'e.g. loud fireworks, late finish'],
  ['budget_priorities', 'Budget priorities', 'e.g. catering, photography'],
  ['dietary_requirements', 'Dietary requirements', 'e.g. vegetarian, Jain meals'],
  ['accessibility_requirements', 'Accessibility needs', 'e.g. step-free access, quiet room'],
]

const emptyForm = {
  event_name: '', event_type: 'birthday', event_date: '', location: '',
  guest_count: '', total_budget: '', preferred_theme: '',
  user_preferences: '', must_have_arrangements: '', things_to_avoid: '',
  budget_priorities: '', dietary_requirements: '', accessibility_requirements: '',
}

function formatDate(value) {
  return new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
    .format(new Date(`${value}T00:00:00`))
}

function money(value) {
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value)
}

function App() {
  const [events, setEvents] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [form, setForm] = useState(emptyForm)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [pageError, setPageError] = useState('')
  const [notice, setNotice] = useState('')
  const [updatingTask, setUpdatingTask] = useState(null)

  useEffect(() => {
    getEvents()
      .then(({ events: saved }) => {
        setEvents(saved)
        if (saved.length) setSelectedId(saved[0].id)
      })
      .catch((error) => setPageError(error.message))
      .finally(() => setLoading(false))
  }, [])

  const selected = events.find((event) => event.id === selectedId)
  const completedCount = selected?.tasks.filter((task) => task.completed).length || 0
  const progress = selected?.tasks.length ? Math.round((completedCount / selected.tasks.length) * 100) : 0

  function updateField(event) {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
    setErrors((current) => ({ ...current, [name]: undefined }))
  }

  async function submitEvent(event) {
    event.preventDefault()
    setPageError('')
    setNotice('')
    setErrors({})
    const payload = {
      ...form,
      guest_count: Number(form.guest_count),
      total_budget: Number(form.total_budget),
    }
    for (const [field] of listFields) {
      payload[field] = form[field].split(/[\n,]/).map((item) => item.trim()).filter(Boolean)
    }
    const clientErrors = {}
    if (!form.event_name.trim()) clientErrors.event_name = 'Add a name for your event.'
    if (!form.event_date || Number.isNaN(Date.parse(`${form.event_date}T00:00:00`))) clientErrors.event_date = 'Choose a valid event date.'
    if (!form.location.trim()) clientErrors.location = 'Add an event location.'
    if (!Number.isInteger(payload.guest_count) || payload.guest_count < 1) clientErrors.guest_count = 'Enter at least one guest.'
    if (!Number.isFinite(payload.total_budget) || payload.total_budget <= 0) clientErrors.total_budget = 'Enter a budget greater than ₹0.'
    if (Object.keys(clientErrors).length) {
      setErrors(clientErrors)
      return
    }

    setSaving(true)
    try {
      const created = await createEvent(payload)
      setEvents((current) => [created, ...current])
      setSelectedId(created.id)
      setForm(emptyForm)
      setNotice(`${created.event_name} is saved. Your planning timeline is ready.`)
    } catch (error) {
      setPageError(error.message)
      setErrors(error.details || {})
    } finally {
      setSaving(false)
    }
  }

  async function toggleTask(task) {
    if (!selected) return
    setUpdatingTask(task.id)
    setPageError('')
    try {
      const updated = await setTaskCompletion(selected.id, task.id, !task.completed)
      setEvents((current) => current.map((event) => event.id === selected.id
        ? { ...event, tasks: event.tasks.map((item) => item.id === updated.id ? updated : item) }
        : event))
    } catch (error) {
      setPageError(error.message)
    } finally {
      setUpdatingTask(null)
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="CelebrAI home"><span className="brand-mark">c</span> celebrai</a>
        <nav aria-label="Main navigation"><a href="#events">My celebrations</a><a href="#create">Create an event</a></nav>
        <span className="currency-tag">INR · ₹</span>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow">A LITTLE LESS TO ORGANIZE</p>
          <h1>Make room<br />for the <em>moment.</em></h1>
          <p className="intro">Thoughtful plans for the people and moments worth celebrating. Start with what matters to you.</p>
          <a className="text-link" href="#create">Plan something lovely <span aria-hidden="true">↗</span></a>
        </div>
        <div className="hero-art" aria-hidden="true"><span className="sun-orb" /><span className="flower flower-one">✳</span><span className="flower flower-two">✳</span><span className="art-caption">made for<br />your moment</span></div>
      </section>

      {(pageError || notice) && <div className={`page-message ${pageError ? 'error' : 'success'}`} role={pageError ? 'alert' : 'status'}>{pageError || notice}</div>}

      <section className="workspace" id="events">
        <div className="events-column">
          <div className="section-heading"><div><p className="eyebrow">YOUR PLANS</p><h2>My celebrations</h2></div><span className="count-pill">{events.length} {events.length === 1 ? 'event' : 'events'}</span></div>
          {loading ? <p className="muted-card" role="status">Gathering your celebrations…</p>
            : events.length === 0 ? <div className="empty-card"><span className="empty-icon" aria-hidden="true">✳</span><h3>Your next favourite memory starts here.</h3><p>Create an event to get a practical timeline tailored to your date.</p><a className="text-link" href="#create">Create your first event ↓</a></div>
              : <div className="event-list">{events.map((item) => (
                <button key={item.id} type="button" className={`event-card ${selectedId === item.id ? 'selected' : ''}`} onClick={() => setSelectedId(item.id)} aria-pressed={selectedId === item.id}>
                  <span className="event-date-tile"><span>{formatDate(item.event_date).split(' ')[0]}</span><strong>{formatDate(item.event_date).split(' ')[1]}</strong></span>
                  <span className="event-card-copy"><strong>{item.event_name}</strong><span>{item.event_type} · {item.location}</span></span>
                  <span className="event-chevron" aria-hidden="true">↗</span>
                </button>
              ))}</div>}

          {selected && <section className="plan-panel" aria-labelledby="plan-title">
            <div className="section-heading plan-heading"><div><p className="eyebrow">YOUR PLANNING RHYTHM</p><h2 id="plan-title">The next steps</h2></div><span className="progress-label">{progress}% done</span></div>
            <div className="progress-track" role="progressbar" aria-label="Planning tasks completed" aria-valuenow={progress} aria-valuemin="0" aria-valuemax="100"><span style={{ width: `${progress}%` }} /></div>
            <p className="plan-meta">{formatDate(selected.event_date)} <span aria-hidden="true">·</span> {selected.guest_count} guests <span aria-hidden="true">·</span> {money(selected.total_budget)}</p>
            <ul className="task-list">{selected.tasks.length ? selected.tasks.map((task) => (
              <li key={task.id} className={`task-row ${task.completed ? 'is-complete' : ''}`}>
                <label className="task-check"><input type="checkbox" checked={task.completed} disabled={updatingTask === task.id} onChange={() => toggleTask(task)} /><span className="custom-check" aria-hidden="true">{task.completed ? '✓' : ''}</span><span className="sr-only">Mark “{task.title}” {task.completed ? 'incomplete' : 'complete'}</span></label>
                <span className="task-copy"><strong>{task.title}</strong><span>{task.description}</span></span>
                <span className={`task-status ${task.status}`}>{task.completed ? 'Done' : task.status === 'overdue' ? 'Overdue' : formatDate(task.due_date)}</span>
              </li>
            )) : <li className="timeline-note">This event date has passed, so no new preparation tasks were generated.</li>}</ul>
          </section>}
        </div>

        <section className="form-panel" id="create" aria-labelledby="create-title">
          <div className="form-heading"><p className="eyebrow">A GOOD PLAN BEGINS WITH YOU</p><h2 id="create-title">What are we<br /><em>celebrating?</em></h2><p>Share the details you know. You can always change your plans later.</p></div>
          <form onSubmit={submitEvent} noValidate>
            <div className="form-grid">
              <Field label="Event name" name="event_name" value={form.event_name} onChange={updateField} placeholder="e.g. Mira’s 30th" error={errors.event_name} required />
              <div className="field"><label htmlFor="event_type">Occasion <span className="required">*</span></label><select id="event_type" name="event_type" value={form.event_type} onChange={updateField}><option value="birthday">Birthday</option><option value="wedding">Wedding</option><option value="anniversary">Anniversary</option><option value="community">Community gathering</option></select></div>
              <Field label="Date" name="event_date" type="date" value={form.event_date} onChange={updateField} error={errors.event_date} required />
              <Field label="Location" name="location" value={form.location} onChange={updateField} placeholder="City or neighbourhood" error={errors.location} required />
              <Field label="Guest count" name="guest_count" type="number" min="1" step="1" value={form.guest_count} onChange={updateField} placeholder="e.g. 40" error={errors.guest_count} required />
              <Field label="Total budget (₹)" name="total_budget" type="number" min="0.01" step="0.01" value={form.total_budget} onChange={updateField} placeholder="e.g. 50000" error={errors.total_budget} required />
              <div className="field full"><Field label="Theme or feeling" name="preferred_theme" value={form.preferred_theme} onChange={updateField} placeholder="e.g. garden brunch, warm and intimate" error={errors.preferred_theme} /></div>
              {listFields.map(([name, label, placeholder]) => <div className="field full" key={name}><label htmlFor={name}>{label}</label><textarea id={name} name={name} value={form[name]} onChange={updateField} placeholder={placeholder} rows="2" aria-invalid={Boolean(errors[name])} aria-describedby={errors[name] ? `${name}-error` : undefined} />{errors[name] && <span className="field-error" id={`${name}-error`}>{errors[name]}</span>}</div>)}
            </div>
            <p className="form-hint">For lists, separate ideas with commas or put each on a new line. Your budget is stored in INR.</p>
            <button className="submit-button" type="submit" disabled={saving}>{saving ? 'Saving your event…' : 'Create my event'} <span aria-hidden="true">↗</span></button>
          </form>
        </section>
      </section>
      <footer><span>celebrai</span><span>Make the moments count.</span></footer>
    </main>
  )
}

function Field({ label, name, type = 'text', value, onChange, placeholder, error, required, min, step }) {
  return <div className="field"><label htmlFor={name}>{label}{required && <span className="required"> *</span>}</label><input id={name} name={name} type={type} value={value} onChange={onChange} placeholder={placeholder} required={required} min={min} step={step} aria-invalid={Boolean(error)} aria-describedby={error ? `${name}-error` : undefined} />{error && <span className="field-error" id={`${name}-error`}>{error}</span>}</div>
}

createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>)
