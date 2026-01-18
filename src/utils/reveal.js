/**
 * Scroll-Triggered Reveal Animation
 * - Activates on first scroll OR 800ms failsafe.
 * - No intersection observer.
 * - Runs once.
 */

let hasTriggered = false

export const initReveal = () => {
  // Check for reduced motion preference
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (prefersReducedMotion) {
    return
  }

  const elements = document.querySelectorAll('.reveal')
  if (!elements || elements.length === 0) return

  // Mark ready
  elements.forEach((el) => {
    el.setAttribute('data-ready', 'true')
  })

  const triggerAnimateIn = () => {
    if (hasTriggered) return
    hasTriggered = true

    // Remove listener
    window.removeEventListener('scroll', handleScroll)

    // Trigger animation with optional stagger
    requestAnimationFrame(() => {
      elements.forEach((el, index) => {
        // Simple stagger: 50ms per element, capped at some limit to avoid long delays
        // or just apply all at once if user prefers "no lock".
        // User said "Add class .animate-in... with stagger" in previous prompt, but "animate-in to all.. automatically" in this one.
        // I will add a very subtle stagger to make it look premium but fast.
        setTimeout(() => {
          el.classList.add('animate-in')
        }, index * 30) // 30ms stagger
      })
    })
  }

  const handleScroll = () => {
    triggerAnimateIn()
  }

  // Listen for first scroll
  window.addEventListener('scroll', handleScroll, { once: true, passive: true })

  // Failsafe: Auto-trigger after 800ms if no scroll
  setTimeout(() => {
    if (!hasTriggered) {
      triggerAnimateIn()
    }
  }, 800)
}

export const disconnectReveal = () => {
  // Nothing to cleanup since listener is {once: true} and variable handles state
  hasTriggered = false
}
