function pad2(value: number): string {
  return value < 10 ? `0${value}` : String(value)
}

function formatFromParts(
  year: number,
  month: number,
  day: number,
  hour: number,
  minute: number,
  second?: number
): string {
  const time = `${pad2(hour)}:${pad2(minute)}`
  return second === undefined
    ? `${year}-${pad2(month)}-${pad2(day)} ${time}`
    : `${year}-${pad2(month)}-${pad2(day)} ${time}:${pad2(second)}`
}

export function formatDisplayDate(value: string | number | Date | null | undefined): string {
  if (value === null || value === undefined || value === '') {
    return ''
  }

  if (value instanceof Date) {
    return formatFromParts(
      value.getFullYear(),
      value.getMonth() + 1,
      value.getDate(),
      value.getHours(),
      value.getMinutes(),
      value.getSeconds()
    )
  }

  if (typeof value === 'number') {
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) {
      return String(value)
    }
    return formatDisplayDate(date)
  }

  const text = String(value).trim()
  if (!text) {
    return ''
  }

  const localLike = text.match(
    /^(\d{4})[-/](\d{2})[-/](\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?$/
  )
  if (localLike) {
    const [, y, m, d, hh = '00', mm = '00', ss] = localLike
    return formatFromParts(
      Number(y),
      Number(m),
      Number(d),
      Number(hh),
      Number(mm),
      ss !== undefined ? Number(ss) : undefined
    )
  }

  const date = new Date(text)
  if (!Number.isNaN(date.getTime())) {
    return formatDisplayDate(date)
  }

  return text
}

