import { useCopilotAction } from '@copilotkit/react-core'

import { useEventSchedule } from '../contexts/EventScheduleContext'
import { normalizeSchedule } from '../lib/eventSchedule'

export function EventScheduleTools() {
  const { setSchedule } = useEventSchedule()

  useCopilotAction({
    name: 'update_event_schedule',
    description:
      'Update the calendar with suggested Meetup events for the user. Call after searching events.',
    parameters: [
      {
        name: 'title',
        type: 'string',
        description: 'Short name for the suggested schedule',
        required: false,
      },
      {
        name: 'events',
        type: 'object[]',
        description: 'Events to show on the calendar',
        required: true,
        attributes: [
          {
            name: 'meetup_event_id',
            type: 'string',
            description: 'Meetup event id from search results',
            required: true,
          },
          {
            name: 'title',
            type: 'string',
            description: 'Event title',
            required: true,
          },
          {
            name: 'start_at',
            type: 'string',
            description: 'ISO datetime for event start',
            required: false,
          },
          {
            name: 'url',
            type: 'string',
            description: 'Meetup event URL',
            required: true,
          },
          {
            name: 'venue',
            type: 'string',
            description: 'Venue name',
            required: false,
          },
          {
            name: 'city',
            type: 'string',
            description: 'City',
            required: false,
          },
          {
            name: 'reason',
            type: 'string',
            description: 'Why this event fits the user request',
            required: false,
          },
        ],
      },
    ],
    handler: async ({ title, events }) => {
      const schedule = normalizeSchedule({ title, events })
      setSchedule(schedule)
      return `Calendar updated with ${schedule.events.length} events.`
    },
  })

  return null
}
