/** Extract plain text from CopilotKit / AG-UI message content. */
export function extractMessageText(content: unknown): string {
  if (typeof content === 'string') {
    return content
  }
  if (!Array.isArray(content)) {
    return ''
  }
  return content
    .map((part) => {
      if (typeof part !== 'object' || part === null) {
        return ''
      }
      if ('text' in part && typeof part.text === 'string') {
        return part.text
      }
      return ''
    })
    .join('')
}
