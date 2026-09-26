import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import axios from 'axios'
import {
  ResponsiveContainer,
  ComposedChart,
  LineChart,
  AreaChart,
  Line,
  Area,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine
} from 'recharts'
import './styles.css'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
})

// Custom Tooltip for Feasible Insights
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    const resTonnes = ((data.base_person_waste_kg_day || 0) / 1000).toFixed(2)
    const indTonnes = ((data.industrial_waste_kg_day || 0) / 1000).toFixed(2)
    const treatGapTonnes = (((data.treatment?.treatment_gap_kg_day) || 0) / 1000).toFixed(2)
    const segTonnes = (((data.treatment?.segregated_kg_day) || 0) / 1000).toFixed(2)
    const unsegTonnes = (((data.treatment?.unsegregated_kg_day) || 0) / 1000).toFixed(2)
    const pop = data.effective_population || 0

    return (
      <div style={{
        backgroundColor: '#ffffff',
        padding: '14px 16px',
        border: '1px solid #10b981',
        borderRadius: '12px',
        boxShadow: '0 8px 20px rgba(0,0,0,0.1)',
        fontSize: '0.88rem',
        minWidth: '220px'
      }}>
        <div style={{ fontWeight: 700, color: '#087443', marginBottom: '8px', borderBottom: '1px solid #e2e8f0', paddingBottom: '4px' }}>
          🗓️ Simulation Year {label} ({pop.toLocaleString()} Citizens)
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', margin: '4px 0', fontWeight: 600 }}>
          <span>Total Daily Waste:</span>
          <span style={{ color: '#087443' }}>{data.daily_waste_tonnes} t/day</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', margin: '4px 0', color: '#4b5563' }}>
          <span>• Residential Waste:</span>
          <span>{resTonnes} t/day</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', margin: '4px 0', color: '#4b5563' }}>
          <span>• Industrial Waste:</span>
          <span>{indTonnes} t/day</span>
        </div>
        <div style={{ borderTop: '1px dashed #e2e8f0', marginTop: '6px', paddingTop: '6px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#dc2626', fontWeight: 600 }}>
            <span>Treatment Deficit:</span>
            <span>{treatGapTonnes} t/day</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#2563eb', fontSize: '0.8rem', marginTop: '2px' }}>
            <span>Segregated (Recycled):</span>
            <span>{segTonnes} t/day</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#9a3412', fontSize: '0.8rem', marginTop: '2px' }}>
            <span>Landfill (Unsegregated):</span>
            <span>{unsegTonnes} t/day</span>
          </div>
        </div>
      </div>
    )
  }
  return null
}

function App() {
  const [token, setToken] = useState(localStorage.token || '')
  const [user, setUser] = useState(JSON.parse(localStorage.user || 'null'))
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [location, setLocation] = useState('')
  const [p, setP] = useState({
    total_population: 25000,
    waste_per_person_per_day: 0.5,
    population_growth_rate: 2,
    floating_population: 2000,
    industrial_waste_kg_day: 2000,
    vehicle_count: 10,
    vehicle_capacity_kg: 2000,
    trips_per_vehicle: 1,
    treatment_capacity_kg: 10000,
    segregation_percent: 60
  })

  const [sim, setSim] = useState(null)
  const [answer, setAnswer] = useState('')
  const [question, setQuestion] = useState('')
  const [chartMode, setChartMode] = useState('overview')

  const headers = { Authorization: `Bearer ${token}` }

  useEffect(() => {
    if (token && !user) {
      api.get('/auth/me', { headers: { Authorization: `Bearer ${token}` } })
        .then(r => {
          setUser(r.data)
          localStorage.user = JSON.stringify(r.data)
        })
        .catch(() => {
          localStorage.clear()
          setToken('')
          setUser(null)
        })
    }
  }, [token, user])

  const [locationDetails, setLocationDetails] = useState(null)

  useEffect(() => {
    if (token && !sim) {
      // Fetch initial location or existing dashboard simulation for viewers/users
      api.get('/locations', { headers })
        .then(async r => {
          if (r.data && r.data.length > 0) {
            const loc = r.data[0]
            setLocation(loc.id)
            setLocationDetails(loc)
            const dash = await api.get(`/dashboard/${loc.id}`, { headers })
            if (dash.data?.latest_simulation) {
              setSim(dash.data.latest_simulation)
            }
          }
        })
        .catch(err => console.error('Error fetching initial location/dashboard:', err))
    }
  }, [token, sim])

  const login = async e => {
    e.preventDefault()
    try {
      const r = await api.post('/auth/login', { email, password })
      localStorage.token = r.data.access_token
      localStorage.user = JSON.stringify(r.data.user)
      setToken(r.data.access_token)
      setUser(r.data.user)
    } catch (err) {
      alert(err.response?.data?.detail || 'Login failed')
    }
  }

  const canSimulate = Boolean(user && user.role !== 'VIEWER')

  const [fieldErrors, setFieldErrors] = useState({})

  const validateFields = (currentP = p) => {
    const errors = {}

    if (currentP.total_population < 0) {
      errors.total_population = 'Must be 0 or greater'
    }
    if (currentP.waste_per_person_per_day < 0.01) {
      errors.waste_per_person_per_day = 'Must be at least 0.01 kg/day'
    } else if (currentP.waste_per_person_per_day > 10) {
      errors.waste_per_person_per_day = 'Cannot exceed 10 kg/day'
    }
    if (currentP.population_growth_rate < -10 || currentP.population_growth_rate > 25) {
      errors.population_growth_rate = 'Must be between -10% and 25%'
    }
    if (currentP.floating_population < 0) {
      errors.floating_population = 'Must be 0 or greater'
    }
    if (currentP.industrial_waste_kg_day < 0) {
      errors.industrial_waste_kg_day = 'Must be 0 or greater'
    }
    if (currentP.vehicle_count < 0) {
      errors.vehicle_count = 'Must be 0 or greater'
    }
    if (currentP.vehicle_capacity_kg <= 0) {
      errors.vehicle_capacity_kg = 'Must be greater than 0 kg'
    }
    if (currentP.trips_per_vehicle < 1) {
      errors.trips_per_vehicle = 'Must be at least 1 trip/day'
    }
    if (currentP.treatment_capacity_kg < 0) {
      errors.treatment_capacity_kg = 'Must be 0 or greater'
    }
    if (currentP.segregation_percent < 0 || currentP.segregation_percent > 100) {
      errors.segregation_percent = 'Must be between 0% and 100%'
    }

    return errors
  }

  const createDemo = async () => {
    if (!canSimulate) {
      alert('Access Restricted: Your role does not have permission to run simulations.')
      return
    }

    const errors = validateFields(p)
    setFieldErrors(errors)

    if (Object.keys(errors).length > 0) {
      return
    }

    try {
      let l = location
      if (!l) {
        const r = await api.post(
          '/locations',
          {
            name: 'Udupi Demonstration',
            location_type: 'Gram Panchayat',
            latitude: 13.3409,
            longitude: 74.7421
          },
          { headers }
        )
        l = r.data.id
        setLocation(l)
      }

      const r = await api.post(
        '/simulations',
        { location_id: l, years: 20, parameters: p },
        { headers }
      )
      setSim(r.data.results)
    } catch (err) {
      console.error('Simulation run failed:', err)
      const detail = err.response?.data?.detail
      if (Array.isArray(detail)) {
        const apiErrors = {}
        detail.forEach(d => {
          const field = d.loc?.at(-1)
          if (field) apiErrors[field] = d.msg
        })
        setFieldErrors(apiErrors)
      } else if (typeof detail === 'string') {
        const userFriendlyMsg = detail === 'Insufficient role permission' 
          ? 'Access Restricted: You do not have permission to perform this action with your current role.'
          : detail
        alert(userFriendlyMsg)
      }
    }
  }

  if (!token) {
    return (
      <main className="login">
        <h1>SWMS</h1>
        <p>Smart Waste Management Simulator</p>
        <form onSubmit={login}>
          <input
            placeholder="Email (e.g. admin@swms.org)"
            onChange={e => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            onChange={e => setPassword(e.target.value)}
            required
          />
          <button type="submit">Sign in</button>
          <small>Register an account through the API docs first at http://localhost:8000/docs</small>
        </form>
      </main>
    )
  }

  const rows = sim?.years || []

  // Derived threshold limits & feasibility insights
  const treatmentCapTonnes = p.treatment_capacity_kg / 1000.0
  const fleetCapTonnes = (p.vehicle_count * p.vehicle_capacity_kg * p.trips_per_vehicle) / 1000.0

  // Prepared chart data rows
  const chartData = rows.map(r => ({
    ...r,
    treatment_capacity_tonnes: treatmentCapTonnes,
    fleet_capacity_tonnes: fleetCapTonnes,
    residential_tonnes: Number(((r.base_person_waste_kg_day || 0) / 1000).toFixed(2)),
    industrial_tonnes: Number(((r.industrial_waste_kg_day || 0) / 1000).toFixed(2)),
    treatment_gap_tonnes: Number((((r.treatment?.treatment_gap_kg_day) || 0) / 1000).toFixed(2)),
    segregated_tonnes: Number((((r.treatment?.segregated_kg_day) || 0) / 1000).toFixed(2)),
    unsegregated_tonnes: Number((((r.treatment?.unsegregated_kg_day) || 0) / 1000).toFixed(2))
  }))

  const fleetBreachRow = chartData.find(item => item.daily_waste_tonnes > fleetCapTonnes)
  const fleetBreachYear = fleetBreachRow ? fleetBreachRow.year : null
  const total20YrCumulativeTonnes = Math.round(
    chartData.reduce((acc, item) => acc + item.daily_waste_tonnes * 365.25, 0)
  )

  return (
    <main>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <b>SWMS</b>
          <span>Decision support for waste planning</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {user && (
            <span style={{
              fontSize: '0.82rem',
              padding: '4px 10px',
              borderRadius: '20px',
              backgroundColor: canSimulate ? '#e0f2fe' : '#f3f4f6',
              color: canSimulate ? '#0369a1' : '#4b5563',
              fontWeight: 600,
              border: `1px solid ${canSimulate ? '#bae6fd' : '#e5e7eb'}`
            }}>
              👤 {user.name} ({user.role})
            </span>
          )}
          <button
            onClick={() => {
              localStorage.clear()
              setToken('')
              setUser(null)
            }}
          >
            Sign out
          </button>
        </div>
      </header>

      <section className="hero">
        <h1>Plan capacity before it becomes a crisis.</h1>
        <p>Every chart is calculated from your saved planning inputs.</p>
      </section>

      {/* Planning Inputs (Only visible to authorized roles like SUPER_ADMIN, MUNICIPAL_AUTHORITY, PANCHAYAT_AUTHORITY, PLANNER) */}
      {canSimulate && (
        <section className="grid inputs">
          <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h2>Planning inputs</h2>
          </div>
          {Object.entries(p).map(([k, v]) => {
            const config = {
              total_population: { min: 0, max: 100000000, step: 100, label: 'total population (citizens)' },
              waste_per_person_per_day: { min: 0.01, max: 10, step: 0.01, label: 'waste per person (kg/day)' },
              population_growth_rate: { min: -10, max: 25, step: 0.1, label: 'population growth rate (%)' },
              floating_population: { min: 0, max: 10000000, step: 50, label: 'floating population (people)' },
              industrial_waste_kg_day: { min: 0, max: 10000000, step: 100, label: 'industrial waste (kg/day)' },
              vehicle_count: { min: 0, max: 10000, step: 1, label: 'vehicle count (trucks)' },
              vehicle_capacity_kg: { min: 1, max: 100000, step: 100, label: 'vehicle capacity (kg/trip, min 1)' },
              trips_per_vehicle: { min: 1, max: 20, step: 1, label: 'trips per vehicle/day (min 1)' },
              treatment_capacity_kg: { min: 0, max: 100000000, step: 500, label: 'treatment plant capacity (kg/day)' },
              segregation_percent: { min: 0, max: 100, step: 1, label: 'segregation rate (0-100%)' }
            }[k] || { min: 0, max: 1000000, step: 1, label: k.replaceAll('_', ' ') }

            const hasError = Boolean(fieldErrors[k])

            return (
              <label key={k} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <span>{config.label}</span>
                <input
                  type="number"
                  min={config.min}
                  max={config.max}
                  step={config.step}
                  value={v}
                  style={{
                    borderColor: hasError ? '#ef4444' : undefined,
                    backgroundColor: hasError ? '#fef2f2' : undefined,
                    boxShadow: hasError ? '0 0 0 2px rgba(239, 68, 68, 0.2)' : undefined
                  }}
                  onChange={e => {
                    const val = Number(e.target.value)
                    const newP = { ...p, [k]: val }
                    setP(newP)
                    // Real-time revalidation for modified field
                    const errors = validateFields(newP)
                    setFieldErrors(errors)
                  }}
                />
                {hasError && (
                  <span style={{ fontSize: '0.78rem', color: '#dc2626', fontWeight: 600, marginTop: '2px' }}>
                    ⚠️ {fieldErrors[k]}
                  </span>
                )}
              </label>
            )
          })}
          <button onClick={createDemo}>Run 20-year simulation</button>
        </section>
      )}

      {/* Read-Only Notice if no simulation is loaded yet */}
      {!canSimulate && !sim && (
        <section style={{
          padding: '24px',
          backgroundColor: '#f8fafc',
          border: '1px solid #cbd5e1',
          borderRadius: '12px',
          textAlign: 'center',
          margin: '20px 0'
        }}>
          <h3 style={{ color: '#334155', margin: '0 0 8px 0' }}>📋 Observer / Viewer Mode Active</h3>
          <p style={{ color: '#64748b', margin: 0 }}>
            You are logged in as a <strong>{user?.role}</strong> (read-only view). Published simulation reports and analytics will appear here once saved by an administrator or planner.
          </p>
        </section>
      )}

      {/* Output Results */}
      {sim && (
        <>
          {/* Location Report Header Context */}
          <div style={{
            display: 'flex',
            justify: 'space-between',
            alignItems: 'center',
            backgroundColor: '#ffffff',
            padding: '16px 20px',
            borderRadius: '12px',
            border: '1px solid #e2e8f0',
            marginBottom: '16px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
          }}>
            <div>
              <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Active Region Report
              </span>
              <h3 style={{ margin: '2px 0 0 0', color: '#0f172a', fontSize: '1.25rem' }}>
                📍 {locationDetails?.name || `Location ID #${location}`}
                <span style={{ fontSize: '0.85rem', fontWeight: 500, color: '#087443', marginLeft: '10px', backgroundColor: '#ecfdf5', padding: '2px 8px', borderRadius: '12px' }}>
                  {locationDetails?.location_type || 'Gram Panchayat'}
                </span>
              </h3>
            </div>
            {!canSimulate && (
              <span style={{ fontSize: '0.82rem', color: '#0369a1', backgroundColor: '#e0f2fe', padding: '6px 12px', borderRadius: '20px', fontWeight: 600, border: '1px solid #bae6fd' }}>
                👁️ Official Published 20-Year Plan (Read-Only)
              </span>
            )}
          </div>

          {/* Summary Cards */}
          <section className="cards">
            <Card n={`${rows[0]?.daily_waste_tonnes} t/day`} t="Baseline Waste (Year 0)" />
            <Card n={`${rows.at(-1)?.daily_waste_tonnes} t/day`} t="Projected Waste (Year 20)" />
            <Card n={`${rows[0]?.treatment?.treatment_gap_kg_day?.toLocaleString()} kg/day`} t="Treatment Plant Deficit (Year 0)" />
          </section>

          {/* Upgraded Waste Growth & Feasibility Analysis */}
          <section className="chart">
            <div className="chart-header">
              <div className="chart-title-group">
                <h2>📈 Waste Growth & Feasibility Analysis</h2>
                <span>Multi-vector 20-year projections vs. Infrastructure Limit Thresholds</span>
              </div>

              {/* View Toggle Bar */}
              <div className="chart-mode-tabs">
                <button
                  className={`tab-btn ${chartMode === 'overview' ? 'active' : ''}`}
                  onClick={() => setChartMode('overview')}
                >
                  📊 Total vs Limits
                </button>
                <button
                  className={`tab-btn ${chartMode === 'composition' ? 'active' : ''}`}
                  onClick={() => setChartMode('composition')}
                >
                  🧩 Composition
                </button>
                <button
                  className={`tab-btn ${chartMode === 'segregation' ? 'active' : ''}`}
                  onClick={() => setChartMode('segregation')}
                >
                  ♻️ Segregation
                </button>
                <button
                  className={`tab-btn ${chartMode === 'deficit' ? 'active' : ''}`}
                  onClick={() => setChartMode('deficit')}
                >
                  ⚠️ Daily Deficit
                </button>
              </div>
            </div>

            {/* Feasibility Alert Cards */}
            <div className="insights-grid">
              <div className="insight-box warning">
                <div className="insight-title">⚠️ Treatment Capacity Deficit</div>
                <div>
                  Daily waste (<strong>{rows[0]?.daily_waste_tonnes} t/day</strong>) exceeds treatment limit (<strong>{treatmentCapTonnes} t/day</strong>) starting from <strong>Year 0</strong>.
                </div>
              </div>

              <div className={`insight-box ${fleetBreachYear !== null ? 'warning' : 'success'}`}>
                <div className="insight-title">🚛 Collection Fleet Limit</div>
                <div>
                  {fleetBreachYear !== null
                    ? `Fleet collection capacity (${fleetCapTonnes} t/day) breached at Year ${fleetBreachYear}!`
                    : `Fleet capacity (${fleetCapTonnes} t/day) is sufficient for all 20 years.`}
                </div>
              </div>

              <div className="insight-box info">
                <div className="insight-title">📦 Cumulative 20-Yr Load</div>
                <div>
                  Total 20-year landfill load: <strong>{total20YrCumulativeTonnes.toLocaleString()} tonnes</strong>.
                </div>
              </div>
            </div>

            {/* Dynamic Recharts Visualization */}
            <ResponsiveContainer width="100%" height={360}>
              {chartMode === 'overview' ? (
                <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="year" label={{ value: 'Simulation Years (0 through 20)', position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: 'Daily Waste (tonnes/day)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend verticalAlign="top" height={36} />

                  {/* Red Dashed Treatment Limit Line */}
                  <ReferenceLine
                    y={treatmentCapTonnes}
                    stroke="#dc2626"
                    strokeDasharray="5 5"
                    strokeWidth={2}
                    label={{ value: `Treatment Limit (${treatmentCapTonnes} t/day)`, fill: '#dc2626', position: 'top', fontSize: 12, fontWeight: 700 }}
                  />

                  {/* Indigo Dashed Fleet Limit Line */}
                  <ReferenceLine
                    y={fleetCapTonnes}
                    stroke="#4f46e5"
                    strokeDasharray="4 4"
                    strokeWidth={2}
                    label={{ value: `Fleet Limit (${fleetCapTonnes} t/day)`, fill: '#4f46e5', position: 'top', fontSize: 12, fontWeight: 700 }}
                  />

                  <Area type="monotone" dataKey="daily_waste_tonnes" fill="#d1fae5" stroke="#10b981" fillOpacity={0.4} name="Total Daily Waste (t/day)" />
                  <Line type="monotone" dataKey="daily_waste_tonnes" stroke="#087443" strokeWidth={3} dot={{ r: 4, fill: '#087443' }} activeDot={{ r: 8 }} name="Daily Waste Trend" />
                </ComposedChart>
              ) : chartMode === 'composition' ? (
                <AreaChart data={chartData} margin={{ top: 20, right: 30, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="year" label={{ value: 'Simulation Years (0 through 20)', position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: 'Daily Waste Composition (tonnes)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend verticalAlign="top" height={36} />

                  <Area type="monotone" dataKey="residential_tonnes" stackId="1" stroke="#087443" fill="#10b981" name="Residential Waste (t/day)" />
                  <Area type="monotone" dataKey="industrial_tonnes" stackId="1" stroke="#d97706" fill="#fbbf24" name="Industrial Waste (t/day)" />
                </AreaChart>
              ) : chartMode === 'segregation' ? (
                <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="year" label={{ value: 'Simulation Years (0 through 20)', position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: 'Segregation Tonnage (tonnes/day)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend verticalAlign="top" height={36} />

                  <Bar dataKey="segregated_tonnes" fill="#10b981" name={`Segregated / Recycled (${p.segregation_percent}%)`} radius={[4, 4, 0, 0]} />
                  <Bar dataKey="unsegregated_tonnes" fill="#ef4444" name={`Unsegregated / Landfill (${100 - p.segregation_percent}%)`} radius={[4, 4, 0, 0]} />
                  <Line type="monotone" dataKey="daily_waste_tonnes" stroke="#087443" strokeWidth={2} name="Total Generation" />
                </ComposedChart>
              ) : (
                <AreaChart data={chartData} margin={{ top: 20, right: 30, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="year" label={{ value: 'Simulation Years (0 through 20)', position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: 'Daily Deficit Gap (tonnes/day)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend verticalAlign="top" height={36} />

                  <Area type="monotone" dataKey="treatment_gap_tonnes" stroke="#dc2626" fill="#fecdd3" name="Daily Treatment Deficit (t/day)" />
                </AreaChart>
              )}
            </ResponsiveContainer>
          </section>

          {/* Chatbot Section */}
          <section className="chat">
            <h2>What-if assistant</h2>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
              <input
                type="text"
                value={question}
                onChange={e => setQuestion(e.target.value)}
                placeholder="E.g., What is the annual waste in year 10?"
                style={{ flex: 1, padding: '10px', borderRadius: '6px', border: '1px solid #cbd5e1' }}
                onKeyDown={e => {
                  if (e.key === 'Enter') {
                    document.getElementById('ask-btn').click();
                  }
                }}
              />
              <button
                id="ask-btn"
                onClick={async () => {
                  if (!question.trim()) return;
                  try {
                    const res = await api.post(
                      '/chatbot',
                      {
                        location_id: location,
                        question: question
                      },
                      { headers }
                    )
                    setAnswer(res.data.answer)
                  } catch (err) {
                    setAnswer("Error: " + (err.response?.data?.detail || "Could not get an answer."))
                  }
                }}
                style={{ padding: '10px 20px' }}
              >
                Ask
              </button>
            </div>
            {answer && (
              <div style={{ padding: '16px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', color: '#166534' }}>
                <strong style={{ display: 'block', marginBottom: '8px', color: '#15803d' }}>🤖 Assistant Answer:</strong> 
                {answer}
              </div>
            )}
          </section>
        </>
      )}
    </main>
  )
}

function Card({ n, t }) {
  return (
    <article>
      <strong>{n}</strong>
      <span>{t}</span>
    </article>
  )
}

createRoot(document.getElementById('root')).render(<App />)
