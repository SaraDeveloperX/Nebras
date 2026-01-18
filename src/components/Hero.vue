<script setup>
import { ref, onMounted } from 'vue'

const isVisible = ref(false)
const isBreathing = ref(false)

onMounted(() => {
  // 1. Respect Reduced Motion - STRICT DISABLE
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    isVisible.value = true // Show immediately without animation
    return
  }

  // 2. Trigger Reveal
  requestAnimationFrame(() => {
    isVisible.value = true

    // 3. Trigger Breathing AFTER reveal (650ms transition)
    // Using timeout to ensure clean sequencing
    setTimeout(() => {
      isBreathing.value = true
    }, 650)
  })
})
</script>

<template>
  <section class="hero">
    <div class="container hero__container">
      <!-- Text Content -->
      <div class="hero__content">
        <h1 class="hero__title">القرار يبدأ من البيانات</h1>
        <p class="hero__description">
          نحوّل البيانات المالية المعقّدة إلى رؤية تنفيذية واضحة، تكشف الواقع المالي وتوجّه القرار
          بثقة.
        </p>
        <a href="#upload" class="hero__cta"> ابدأ التحليل الآن </a>
      </div>

      <!-- Image -->
      <div class="hero__visual">
        <!-- Wrapper for One-time Reveal -->
        <div class="hero__reveal-layer" :class="{ 'is-visible': isVisible }">
          <!-- Wrapper for Continuous Breathing -->
          <div class="hero__breath-layer" :class="{ 'is-breathing': isBreathing }">
            <img src="@/assets/hero.jpg" alt="Financial Analysis Dashboard" class="hero__image" />
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped lang="scss">
@use 'sass:color';
@use '../styles/variables' as *;

.hero {
  padding: $space-section 0;
  background-color: $color-bg;

  &__container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: $space-3xl;
    align-items: center;

    @media (max-width: 900px) {
      grid-template-columns: 1fr;
      gap: $space-2xl;
    }
  }

  &__content {
    display: flex;
    flex-direction: column;
    align-items: flex-start;

    @media (max-width: 900px) {
      align-items: center;
      text-align: center;
    }
  }

  &__title {
    font-size: 3.5rem;
    font-weight: 800;
    line-height: 1.2;
    margin-bottom: $space-lg;
    color: $color-text;

    @media (max-width: 480px) {
      font-size: 2.5rem;
    }
  }

  &__description {
    font-size: 1.125rem;
    line-height: 1.75;
    color: $color-text-secondary; // Solid grey
    margin-bottom: $space-xl;
    max-width: 520px;
  }

  &__cta {
    background-color: $surface;
    color: $color-text;
    border: 1px solid $color-border;
    height: 44px;
    padding: 0 $space-xl;
    border-radius: $radius-md;
    font-size: 1rem;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition:
      background-color $t-fast $ease,
      transform $t-fast $ease,
      border-color $t-fast $ease;

    &:hover {
      background-color: $color-card; // Solid hover
      border-color: $color-border-strong;
      transform: translateY(-1px);
    }

    &:focus-visible {
      outline: 2px solid $color-border-strong;
      outline-offset: 3px;
    }

    &:active {
      transform: translateY(0);
    }
  }

  &__visual {
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;
    // Removed radial gradient glow to avoid transparency
  }

  // Layer 1: Entrance Reveal - REMOVED FADE
  &__reveal-layer {
    opacity: 1; // Strict visibility
    transform: none;

    // Kept structure but removed transition logic for strict solidity
  }

  // Layer 2: Continuous Breathing
  &__breath-layer {
    position: relative;
    width: 100%;
    max-width: 520px;
    height: auto;
    transform: translateY(0);

    &.is-breathing {
      animation: heroBreath 8s ease-in-out infinite;
    }

    @media (prefers-reduced-motion: reduce) {
      animation: none;
    }
  }

  &__image {
    width: 100%;
    height: auto;
    object-fit: contain;
    display: block;
  }
}

@keyframes heroBreath {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}
</style>
