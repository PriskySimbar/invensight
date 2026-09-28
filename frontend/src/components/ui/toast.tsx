// This file is kept for compatibility but we use sonner for toasts
// The actual toast implementation is in layout.tsx using sonner
export const toast = {
  create: () => {},
}

export const useToastManager = () => ({
  toasts: [],
})

export const Toaster = () => null
