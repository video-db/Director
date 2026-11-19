// Upload Dropzone. The root's data-state is idle, dragover, error or uploading; data-disabled when disabled.
export type UploadDropzoneTone = 'disabled' | 'error' | 'dragover' | 'default'

export const uploadDropzoneClasses = [
  'flex w-full cursor-pointer flex-col items-center gap-16 rounded-sm border-2 border-dashed px-48 py-20 text-center transition-colors duration-150',
  'border-border-neutral-hover bg-background-neutral-subtle',
  // Hover only while it can take files: not while uploading or disabled.
  'not-data-disabled:not-data-[state=uploading]:hover:border-border-brand-primary',
  'data-[state=dragover]:border-border-brand-primary data-[state=dragover]:bg-background-brand-tertiary',
  'data-[state=error]:border-border-error-primary data-[state=error]:bg-background-error-subtle',
  'data-[state=uploading]:cursor-default has-focus-visible:shadow-focus-ring',
  'data-disabled:cursor-not-allowed data-disabled:border-border-neutral-strong data-disabled:bg-background-neutral-secondary',
]

// The role="button" inside: icon and text. The focus ring shows on the root (has-focus-visible).
export const uploadDropzoneButtonClasses = 'flex flex-col items-center gap-16 rounded-xs outline-none'
export const uploadDropzoneGlyphClasses = 'flex size-48 items-center justify-center rounded-full border border-border-neutral-primary bg-background-neutral-primary'
export const uploadDropzoneIconTones: Record<UploadDropzoneTone, string> = {
  disabled: 'text-icon-neutral-disabled',
  error: 'text-icon-error-primary',
  dragover: 'text-icon-brand-primary',
  default: 'text-icon-neutral-primary',
}
export const uploadDropzoneTextClasses = 'flex flex-col gap-4'
export const uploadDropzoneTitleClasses = 'text-sm font-semibold'
export const uploadDropzoneTitleTones: Record<UploadDropzoneTone, string> = {
  disabled: 'text-text-neutral-disabled',
  error: 'text-text-error-primary',
  dragover: 'text-text-brand-strong',
  default: 'text-text-neutral-primary',
}
export const uploadDropzoneDescriptionClasses = 'text-xs'
export const uploadDropzoneDescriptionTones = { disabled: 'text-text-neutral-disabled', enabled: 'text-text-neutral-secondary' }
export const uploadDropzoneProgressClasses = 'max-w-320'
