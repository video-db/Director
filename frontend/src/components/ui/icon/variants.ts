/**
 * Inline style for an icon: Material Symbols Outlined at weight 300 and grade 0 (the console spec),
 * with the optical size following the rendered size.
 */
export function iconStyle(size: number, filled: boolean) {
  return {
    fontSize: `${size}px`,
    width: `${size}px`,
    height: `${size}px`,
    fontVariationSettings: `'FILL' ${filled ? 1 : 0}, 'wght' 300, 'GRAD' 0, 'opsz' ${Math.min(48, Math.max(20, size))}`,
  }
}
