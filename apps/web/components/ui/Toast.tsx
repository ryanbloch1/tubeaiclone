"use client";

import { useEffect, useState } from 'react';
import { X, Undo2 } from 'lucide-react';

export type ToastVariant = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  message: string;
  variant: ToastVariant;
  duration?: number;
  onUndo?: () => void;
  undoLabel?: string;
}

interface ToastProps {
  toast: Toast;
  onRemove: (id: string) => void;
}

const variantStyles = {
  success: 'bg-green-50 border-green-200 text-green-800',
  error: 'bg-red-50 border-red-200 text-red-800',
  info: 'bg-blue-50 border-blue-200 text-blue-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
};

const variantIcons = {
  success: '✅',
  error: '❌',
  info: 'ℹ️',
  warning: '⚠️',
};

export function ToastComponent({ toast, onRemove }: ToastProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [timeLeft, setTimeLeft] = useState(toast.duration || 5000);

  useEffect(() => {
    // Animate in
    const showTimer = setTimeout(() => setIsVisible(true), 10);
    
    // Auto-dismiss timer
    const dismissTimer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(() => onRemove(toast.id), 300); // Wait for animation
    }, toast.duration || 5000);

    // Countdown for undo button
    const countdownInterval = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1000) {
          clearInterval(countdownInterval);
          return 0;
        }
        return prev - 1000;
      });
    }, 1000);

    return () => {
      clearTimeout(showTimer);
      clearTimeout(dismissTimer);
      clearInterval(countdownInterval);
    };
  }, [toast.id, toast.duration, onRemove]);

  const handleUndo = () => {
    if (toast.onUndo) {
      toast.onUndo();
    }
    onRemove(toast.id);
  };

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => onRemove(toast.id), 300);
  };

  return (
    <div
      className={`
        transform transition-all duration-300 ease-in-out
        ${isVisible 
          ? 'translate-x-0 opacity-100 scale-100' 
          : 'translate-x-full opacity-0 scale-95'
        }
        max-w-sm w-full bg-white border rounded-lg shadow-lg p-4
        ${variantStyles[toast.variant]}
      `}
    >
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0 text-lg">
          {variantIcons[toast.variant]}
        </div>
        
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium break-words">
            {toast.message}
          </p>
          
          {toast.onUndo && timeLeft > 0 && (
            <div className="mt-2 flex items-center space-x-2">
              <button
                onClick={handleUndo}
                className="text-xs font-medium underline hover:no-underline focus:outline-none"
              >
                <Undo2 className="w-3 h-3 inline mr-1" />
                {toast.undoLabel || 'Undo'} ({Math.ceil(timeLeft / 1000)}s)
              </button>
            </div>
          )}
        </div>
        
        <button
          onClick={handleClose}
          className="flex-shrink-0 text-gray-400 hover:text-gray-600 focus:outline-none"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

interface ToastContainerProps {
  toasts: Toast[];
  onRemove: (id: string) => void;
}

export function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {toasts.map((toast) => (
        <ToastComponent
          key={toast.id}
          toast={toast}
          onRemove={onRemove}
        />
      ))}
    </div>
  );
}


