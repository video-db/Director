import { v1 } from 'uuid'

export function secondsToHHMMSS(val) {
  if (!val) return '00:00:00'
  let time = ''
  time = new Date(val * 1000).toISOString().substring(11, 19)
  if (time.substring(0, 2) === '00') {
    return time.substring(3, time.length)
  }
  return time
}

export function randomHsl(num, total) {
  return 'hsla(' + ((num + 1) / (total + 1)) * 360 + ', 100%, 50%, 1)'
}

export function separateBulletPoints(markdownString) {
  // Split the markdown string into individual lines
  const lines = markdownString.split('\n')

  // Remove empty lines and trim leading/trailing whitespace from each line
  const cleanedLines = lines
    .filter((line) => line.trim() !== '')
    .map((line) => line.trim())

  // Iterate over the cleaned lines and extract the bullet points
  const bulletPoints = []
  let currentBulletPoint = ''

  cleanedLines.forEach((line) => {
    if (line.startsWith('-')) {
      // Add the current bullet point to the array
      if (currentBulletPoint !== '') {
        bulletPoints.push(currentBulletPoint.trim())
      }

      // Start a new bullet point
      currentBulletPoint = line.substring(1).trim()
    } else {
      // Append the line to the current bullet point
      currentBulletPoint += ' ' + line.trim()
    }
  })

  // Add the last bullet point to the array
  if (currentBulletPoint !== '') {
    bulletPoints.push(currentBulletPoint.trim())
  }

  return bulletPoints
}

const NOT_ALLOWED_CHARS = ['\\$', '#', '\\[', '\\]', '\\.', '/'] // Escape special characters with backslashes

export function generateSlug(title) {
  if (title.split(' ').length > 1) {
    const nTitle = title
      .split(' ')
      .slice(0, 10)
      .filter((w) => /^[a-zA-Z0-9]+$/.test(w))
      .join('-')
    title = nTitle
  }

  for (const NOT_ALLOWED_CHAR of NOT_ALLOWED_CHARS) {
    title = title.replace(new RegExp(NOT_ALLOWED_CHAR, 'g'), '-')
  }

  const key = v1().replace(/-/g, '').substring(0, 8)
  const slug = `${title}_${key}`
  return slug
}

export default {}
