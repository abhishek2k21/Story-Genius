import { Component, type ErrorInfo, type ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { AlertTriangle } from 'lucide-react';

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            return (
                <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 text-white p-4">
                    <div className="max-w-md text-center space-y-6">
                        <div className="flex justify-center">
                            <div className="bg-red-900/20 p-4 rounded-full border border-red-900/50">
                                <AlertTriangle className="h-10 w-10 text-red-500" />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <h1 className="text-2xl font-bold">Something went wrong</h1>
                            <p className="text-slate-400">
                                {this.state.error?.message || "An unexpected error occurred. Please try again."}
                            </p>
                        </div>

                        <div className="flex gap-4 justify-center">
                            <Button
                                onClick={() => window.location.reload()}
                                variant="default"
                                className="bg-white text-black hover:bg-slate-200"
                            >
                                Reload Page
                            </Button>
                            <Button
                                onClick={() => window.location.href = '/'}
                                variant="outline"
                                className="border-slate-800 hover:bg-slate-900"
                            >
                                Go Home
                            </Button>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
