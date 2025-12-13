import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import type { User, LoginRequest, SignupRequest } from '../types';
import { login as apiLogin, signup as apiSignup, getCurrentUser, logout as apiLogout, getStoredToken, setStoredToken } from '../api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  signup: (data: SignupRequest) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
  setToken: (token: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const checkAuth = async () => {
      const token = getStoredToken();
      if (token) {
        try {
          const currentUser = await getCurrentUser();
          setUser(currentUser);
        } catch {
          // Token is invalid
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (credentials: LoginRequest) => {
    const response = await apiLogin(credentials);
    setUser(response.user);
  };

  const signup = async (data: SignupRequest) => {
    const response = await apiSignup(data);
    setUser(response.user);
  };

  const logout = () => {
    setUser(null);
    apiLogout();
  };

  const setToken = async (token: string) => {
    setStoredToken(token);
    // Fetch user info with the new token
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      console.error('Failed to get user info:', error);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        signup,
        logout,
        setUser,
        setToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
