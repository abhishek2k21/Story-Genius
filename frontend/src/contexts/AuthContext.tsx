import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { apiClient } from '@/lib/api-client';

interface User {
    id: string;
    email: string;
    full_name: string | null;
    is_verified: boolean;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    login: (email: string, password: string) => Promise<void>;
    signup: (email: string, password: string, fullName?: string) => Promise<void>;
    logout: () => void;
    isAuthenticated: boolean;
    isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Load token from localStorage on mount
    useEffect(() => {
        const storedToken = localStorage.getItem('auth_token');
        if (storedToken) {
            setToken(storedToken);
            apiClient.setToken(storedToken);
            fetchUser();
        } else {
            setIsLoading(false);
        }
    }, []);

    const fetchUser = async () => {
        try {
            const userData = await apiClient.getCurrentUser();
            setUser(userData);
        } catch (error) {
            // Token invalid, clear it
            localStorage.removeItem('auth_token');
            setToken(null);
        } finally {
            setIsLoading(false);
        }
    };

    const login = async (email: string, password: string) => {
        const response = await apiClient.login(email, password);
        setToken(response.access_token);
        setUser(response.user);
        localStorage.setItem('auth_token', response.access_token);
        apiClient.setToken(response.access_token);
    };

    const signup = async (email: string, password: string, fullName?: string) => {
        const response = await apiClient.signup(email, password, fullName);
        setToken(response.access_token);
        setUser(response.user);
        localStorage.setItem('auth_token', response.access_token);
        apiClient.setToken(response.access_token);
    };

    const logout = () => {
        setUser(null);
        setToken(null);
        localStorage.removeItem('auth_token');
        apiClient.setToken(null);
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                token,
                login,
                signup,
                logout,
                isAuthenticated: !!user,
                isLoading,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
}
