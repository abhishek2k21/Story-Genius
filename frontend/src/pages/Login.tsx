import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useNavigate } from 'react-router-dom'

export default function Login() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const navigate = useNavigate()

    const handleLogin = async () => {
        // Mock login
        console.log("Logging in...", email)
        localStorage.setItem('token', 'mock-token-123')
        navigate('/dashboard')
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4">
            <Card className="w-full max-w-sm">
                <CardHeader>
                    <CardTitle className="text-2xl font-bold text-center">Story Genius</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        <div className="space-y-2">
                            <Input
                                placeholder="Email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                type="email"
                            />
                        </div>
                        <div className="space-y-2">
                            <Input
                                type="password"
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                        <Button onClick={handleLogin} className="w-full">
                            Sign In
                        </Button>
                        <div className="text-center text-sm text-muted-foreground">
                            Mock Login: Any email/password works
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}
