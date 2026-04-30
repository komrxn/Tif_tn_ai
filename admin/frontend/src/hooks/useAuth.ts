import { login as apiLogin } from '../api/auth'

const KEY = 'admin_token'

export function useAuth() {
  const isAuthenticated = (): boolean => !!localStorage.getItem(KEY)

  const login = async (username: string, password: string): Promise<void> => {
    const token = await apiLogin(username, password)
    localStorage.setItem(KEY, token)
  }

  const logout = (): void => {
    localStorage.removeItem(KEY)
    window.location.href = '/login'
  }

  return { isAuthenticated, login, logout }
}
