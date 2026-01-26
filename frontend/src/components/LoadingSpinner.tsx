import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
    size?: 'sm' | 'default' | 'lg';
    className?: string;
}

export function LoadingSpinner({ size = 'default', className = '' }: LoadingSpinnerProps) {
    const sizeClasses = {
        sm: 'h-4 w-4',
        default: 'h-8 w-8',
        lg: 'h-12 w-12'
    };

    return (
        <div className={`flex items-center justify-center ${className}`}>
            <Loader2 className={`animate-spin text-primary ${sizeClasses[size]}`} />
        </div>
    );
}
