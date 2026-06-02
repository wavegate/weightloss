import { QueryClient, focusManager } from '@tanstack/react-query'

// React Query only listens to visibilitychange by default. Also listen to window
// focus so refetch runs when you click back into the browser from another app.
focusManager.setEventListener((handleFocus) => {
  if (typeof window === 'undefined') {
    return
  }

  const onFocus = () => handleFocus()

  window.addEventListener('visibilitychange', onFocus)
  window.addEventListener('focus', onFocus)

  return () => {
    window.removeEventListener('visibilitychange', onFocus)
    window.removeEventListener('focus', onFocus)
  }
})

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnMount: 'always',
      refetchOnWindowFocus: 'always',
      retry: 1,
    },
  },
})
