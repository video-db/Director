export type LogoBrand = 'videodb' | 'director'
export type LogoLockup = 'combination' | 'icon'
export type LogoTheme = 'auto' | 'light' | 'dark'

// theme="auto" renders both artworks and shows one. It switches on the .dark class the tokens use, not
// the project's dark: variant, which with tokens.scoped.css can follow the OS setting instead.
export const logoClasses = {
  /** The light artwork with theme="auto": hidden inside .dark */
  autoLight: 'w-auto shrink-0 [&:where(.dark,.dark_*)]:hidden',
  /** The dark artwork with theme="auto": shown only inside .dark */
  autoDark: 'hidden w-auto shrink-0 [&:where(.dark,.dark_*)]:block',
  /** theme="light" or "dark": one artwork, always shown */
  fixed: 'w-auto shrink-0',
} as const
