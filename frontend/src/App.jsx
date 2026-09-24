import './App.css'
import { AuthScreen } from './components/AuthScreen'
import { Dashboard } from './components/Dashboard'
import { useAuth } from './hooks/useAuth'

function App() {
  const { user, isRestoring, login, logout, register } = useAuth()

  if (isRestoring) {
    return <main className="loading-screen" role="status">Restoring your session…</main>
  }

  if (user) {
    return <Dashboard user={user} onLogout={logout} />
  }

  return <AuthScreen onLogin={login} onRegister={register} />
}

export default App

