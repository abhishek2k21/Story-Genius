import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';

export default function Signup() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const { signup } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (password.length < 8) {
            toast.error('Password must be at least 8 characters');
            return;
        }

        setIsLoading(true);

        try {
            await signup(email, password, fullName);
            toast.success('Account created! Welcome to Story Genius.');
            navigate('/dashboard');
        } catch (error) {
            toast.error('Signup failed', {
                description: error instanceof Error ? error.message : 'Could not create account',
            });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-slate-950">
            <Card className="w-full max-w-md bg-slate-900 border-slate-800">
                <CardHeader>
                    <CardTitle className="text-2xl text-center bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                        Create your account
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="text-sm font-medium text-slate-200">Full Name</label>
                            <Input
                                type="text"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                placeholder="John Doe"
                                className="bg-slate-950 border-slate-700 text-white"
                            />
                        </div>
                        <div>
                            <label className="text-sm font-medium text-slate-200">Email</label>
                            <Input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="you@example.com"
                                className="bg-slate-950 border-slate-700 text-white"
                                required
                            />
                        </div>
                        <div>
                            <label className="text-sm font-medium text-slate-200">Password</label>
                            <Input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                className="bg-slate-950 border-slate-700 text-white"
                                required
                                minLength={8}
                            />
                            <p className="text-xs text-slate-500 mt-1">
                                Minimum 8 characters
                            </p>
                        </div>
                        <Button type="submit" className="w-full" disabled={isLoading}>
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Creating account...
                                </>
                            ) : (
                                'Sign up'
                            )}
                        </Button>
                    </form>
                    <p className="text-sm text-center mt-4 text-slate-400">
                        Already have an account?{' '}
                        <Link to="/login" className="text-blue-400 underline hover:text-blue-300">
                            Login
                        </Link>
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}
