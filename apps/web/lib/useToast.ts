"use client";

import { useState, useCallback } from 'react';
import { Toast, ToastVariant } from '@/components/ui/Toast';

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((
    message: string,
    variant: ToastVariant = 'info',
    options?: {
      duration?: number;
      onUndo?: () => void;
      undoLabel?: string;
    }
  ) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newToast: Toast = {
      id,
      message,
      variant,
      duration: options?.duration || 5000,
      onUndo: options?.onUndo,
      undoLabel: options?.undoLabel,
    };

    setToasts(prev => [...prev, newToast]);
    return id;
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const success = useCallback((message: string, options?: { duration?: number; onUndo?: () => void; undoLabel?: string }) => {
    return addToast(message, 'success', options);
  }, [addToast]);

  const error = useCallback((message: string, options?: { duration?: number; onUndo?: () => void; undoLabel?: string }) => {
    return addToast(message, 'error', options);
  }, [addToast]);

  const info = useCallback((message: string, options?: { duration?: number; onUndo?: () => void; undoLabel?: string }) => {
    return addToast(message, 'info', options);
  }, [addToast]);

  const warning = useCallback((message: string, options?: { duration?: number; onUndo?: () => void; undoLabel?: string }) => {
    return addToast(message, 'warning', options);
  }, [addToast]);

  const clearAll = useCallback(() => {
    setToasts([]);
  }, []);

  return {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    info,
    warning,
    clearAll,
  };
}


