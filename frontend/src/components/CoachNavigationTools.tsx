import { useCopilotAction } from '@copilotkit/react-core'
import { useNavigate } from 'react-router-dom'

const PAGE_ROUTES = {
  measurements: '/measurements',
  food: '/food',
  metabolism: '/metabolism',
} as const

type AppPage = keyof typeof PAGE_ROUTES

export function CoachNavigationTools() {
  const navigate = useNavigate()

  useCopilotAction({
    name: 'navigate_to_page',
    description:
      'Navigate the user to a section of the weight loss app (measurements, food, or metabolism).',
    parameters: [
      {
        name: 'page',
        type: 'string',
        description:
          'Which page to open: measurements, food, or metabolism',
        required: true,
      },
    ],
    handler: async ({ page }) => {
      const path = PAGE_ROUTES[page as AppPage]
      if (!path) {
        return `Unknown page "${page}". Use measurements, food, or metabolism.`
      }
      navigate(path)
      return `Opened the ${page} page.`
    },
  })

  return null
}
