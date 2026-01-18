/**
 * Continuous Scroll-Linked Motion
 * - Driven by requestAnimationFrame.
 * - Updates CSS variables --op (opacity) and --ty (translateY).
 * - No "locking" or state classes. Purely continuous.
 */

let rafId = null
let elements = []
let windowHeight = 0
let isReducedMotion = false
let isMobile = false

// Configuration
const CONFIG = {
  mobileBreakpoint: 768,
  opacityFloor: 0.2, // Never fully invisible
  // Max translation
  tySection: 18,
  tyItem: 22,
  tyMobileSection: 12,
  tyMobileItem: 16,
  // Scale factor (very subtle)
  scaleBase: 0.985,
}

// Check for reduced motion preference
const checkReducedMotion = () => {
  isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

const checkMobile = () => {
  isMobile = window.innerWidth <= CONFIG.mobileBreakpoint
}

const update = () => {
  if (isReducedMotion) return

  elements.forEach((el) => {
    const rect = el.dom.getBoundingClientRect()

    // Calculate visibility progress
    // We want motion when element enters bottom of viewport until it's somewhat fully visible
    // p = 0 (just entering bottom) -> 1 (fully visible or higher up)

    // Simple linear interpolation based on viewport position
    // Let's say we want it to be fully "in" when the top is at 85% of viewport height?
    // Or simpler: standardize 0 to 1 based on entry position.

    // Distance from bottom of viewport
    const distFromBottom = windowHeight - rect.top

    // Define a "motion zone". E.g., first 300px of entry.
    // If distFromBottom < 0, it's below viewport.
    // If distFromBottom > 0, it's entering.

    // We want a normalized 0-1 value.
    // Let's use a "transition distance" of approx 400px (or windowHeight * 0.4)
    const transitionDist = 400

    let p = distFromBottom / transitionDist

    // Clamp p to [0, 1]
    if (p < 0) p = 0
    if (p > 1) p = 1

    // Apply easing? "clamp(0.15 + 0.85*p)" implies linear mapping to opacity range.
    // Opacity: 0.2 -> 1.0
    const op = CONFIG.opacityFloor + (1 - CONFIG.opacityFloor) * p

    // TranslateY: Max -> 0
    // If is section or item
    const maxTy =
      el.type === 'item'
        ? isMobile
          ? CONFIG.tyMobileItem
          : CONFIG.tyItem
        : isMobile
          ? CONFIG.tyMobileSection
          : CONFIG.tySection

    const ty = (1 - p) * maxTy

    // Scale: 0.985 -> 1.0
    const sc = CONFIG.scaleBase + (1 - CONFIG.scaleBase) * p

    // Optimization: Don't write if values haven't changed significantly?
    // For smoothness, we just write. rAF handles it well.
    // Use setProperty for performance.

    // el.dom.style.setProperty('--op', op.toFixed(3))
    // el.dom.style.setProperty('--ty', `${ty.toFixed(1)}px`)

    // Direct style might be slightly faster than var() in some engines?
    // User requested CSS variables approach.
    el.dom.style.setProperty('--op', op.toFixed(3))
    el.dom.style.setProperty('--ty', `${ty.toFixed(2)}px`)
    el.dom.style.setProperty('--sc', sc.toFixed(3))
  })

  rafId = requestAnimationFrame(update)
}

const onResize = () => {
  windowHeight = window.innerHeight
  checkMobile()
}

export const initScrollMotion = () => {
  // HMR Guard
  if (window.__scrollMotionInit) {
    window.__scrollMotionInit() // Cleanup old if exists (re-assignment below handles cleanup logic effectively if we stored it, but mostly we just restart)
    cancelAnimationFrame(rafId)
  }

  checkReducedMotion()
  checkMobile()
  windowHeight = window.innerHeight

  if (isReducedMotion) {
    // Reset any styles if reduced motion
    const all = document.querySelectorAll('[data-motion]')
    all.forEach((el) => {
      el.style.opacity = '1'
      el.style.transform = 'none'
    })
    return
  }

  // Collect Elements
  const motionEls = document.querySelectorAll('[data-motion]')
  elements = Array.from(motionEls).map((el) => ({
    dom: el,
    type: el.getAttribute('data-motion'), // 'section' or 'item'
  }))

  window.addEventListener('resize', onResize, { passive: true })

  // Start Loop
  update()

  // Store cleanup
  window.__scrollMotionInit = () => {
    window.removeEventListener('resize', onResize)
    cancelAnimationFrame(rafId)
  }
}
