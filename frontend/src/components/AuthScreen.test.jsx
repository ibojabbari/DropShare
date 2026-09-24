import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { AuthScreen } from './AuthScreen'

function renderAuthScreen(overrides = {}) {
  const props = {
    onLogin: vi.fn().mockResolvedValue(undefined),
    onRegister: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  }

  render(<AuthScreen {...props} />)
  return props
}

describe('AuthScreen', () => {
  it('shows the sign-in form by default', () => {
    renderAuthScreen()

    expect(screen.getByRole('heading', { name: 'Welcome back' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeTruthy()
  })

  it('switches to the account-creation form', async () => {
    const user = userEvent.setup()
    renderAuthScreen()

    await user.click(screen.getByRole('button', { name: 'Create an account' }))

    expect(screen.getByRole('heading', { name: 'Create your workspace' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Create account' })).toBeTruthy()
  })

  it('submits entered credentials to the login handler', async () => {
    const user = userEvent.setup()
    const onLogin = vi.fn().mockResolvedValue(undefined)
    renderAuthScreen({ onLogin })

    await user.type(screen.getByLabelText('Username'), 'alice')
    await user.type(screen.getByLabelText('Password'), 'CorrectHorseBatteryStaple!2026')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(onLogin).toHaveBeenCalledWith({
      username: 'alice',
      password: 'CorrectHorseBatteryStaple!2026',
    })
  })

  it('shows an error returned by the login handler', async () => {
    const user = userEvent.setup()
    renderAuthScreen({ onLogin: vi.fn().mockRejectedValue(new Error('Invalid username or password.')) })

    await user.type(screen.getByLabelText('Username'), 'alice')
    await user.type(screen.getByLabelText('Password'), 'wrong-password')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByText('Invalid username or password.')).toBeTruthy()
  })

  it('confirms successful registration and returns to sign-in', async () => {
    const user = userEvent.setup()
    const onRegister = vi.fn().mockResolvedValue(undefined)
    renderAuthScreen({ onRegister })

    await user.click(screen.getByRole('button', { name: 'Create an account' }))
    await user.type(screen.getByLabelText('Username'), 'alice')
    await user.type(screen.getByLabelText('Password'), 'CorrectHorseBatteryStaple!2026')
    await user.click(screen.getByRole('button', { name: 'Create account' }))

    expect(onRegister).toHaveBeenCalledWith({
      username: 'alice',
      password: 'CorrectHorseBatteryStaple!2026',
    })
    expect(await screen.findByText('Account created. You can now sign in.')).toBeTruthy()
    expect(screen.getByRole('heading', { name: 'Welcome back' })).toBeTruthy()
    expect(screen.getByLabelText('Username').value).toBe('alice')
    expect(screen.getByLabelText('Password').value).toBe('')
  })
})

