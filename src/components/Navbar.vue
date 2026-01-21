<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const isMenuOpen = ref(false)
const activeSection = ref('overview')

const sections = ['overview', 'how', 'results', 'upload']

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value
}

const closeMenu = () => {
  isMenuOpen.value = false
}

// Close menu on outside click
const handleOutsideClick = (event) => {
  const navbar = document.querySelector('.navbar')
  if (navbar && !navbar.contains(event.target) && isMenuOpen.value) {
    closeMenu()
  }
}

// Scroll-spy: detect which section is in view
const handleScroll = () => {
  const scrollY = window.scrollY + 120

  for (const section of sections) {
    const element = document.getElementById(section)
    if (element) {
      const { offsetTop, offsetHeight } = element
      if (scrollY >= offsetTop && scrollY < offsetTop + offsetHeight) {
        activeSection.value = section
        break
      }
    }
  }
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
  document.addEventListener('click', handleOutsideClick)
  handleScroll()
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
  document.removeEventListener('click', handleOutsideClick)
})
</script>

<template>
  <nav class="navbar">
    <div class="container navbar__container">
      <!-- Zone 1 (Right in RTL): Logo -->
      <a href="#" class="navbar__brand">
        <img src="@/assets/logo.png" alt="نبراس" class="navbar__logo" />
      </a>

      <!-- Zone 2 (Center): Navigation Links -->
      <ul class="navbar__links">
        <li>
          <a
            href="#overview"
            class="navbar__link"
            :class="{ 'navbar__link--active': activeSection === 'overview' }"
            >نظرة عامة</a
          >
        </li>
        <li>
          <a
            href="#how"
            class="navbar__link"
            :class="{ 'navbar__link--active': activeSection === 'how' }"
            >كيف يعمل</a
          >
        </li>
        <li>
          <a
            href="#results"
            class="navbar__link"
            :class="{ 'navbar__link--active': activeSection === 'results' }"
            >النتائج</a
          >
        </li>
      </ul>

      <!-- Mobile: Hamburger -->
      <button
        class="navbar__hamburger"
        @click.stop="toggleMenu"
        :aria-expanded="isMenuOpen"
        aria-label="فتح القائمة"
      >
        <span
          class="navbar__hamburger-line"
          :class="{ 'navbar__hamburger-line--open': isMenuOpen }"
        ></span>
        <span
          class="navbar__hamburger-line"
          :class="{ 'navbar__hamburger-line--open': isMenuOpen }"
        ></span>
        <span
          class="navbar__hamburger-line"
          :class="{ 'navbar__hamburger-line--open': isMenuOpen }"
        ></span>
      </button>
    </div>

    <!-- Mobile Menu -->
    <Transition name="menu">
      <div v-if="isMenuOpen" class="navbar__mobile-menu">
        <ul class="navbar__mobile-links">
          <li><a href="#overview" class="navbar__mobile-link" @click="closeMenu">نظرة عامة</a></li>
          <li><a href="#how" class="navbar__mobile-link" @click="closeMenu">كيف يعمل</a></li>
          <li><a href="#results" class="navbar__mobile-link" @click="closeMenu">النتائج</a></li>
        </ul>
      </div>
    </Transition>
  </nav>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.navbar {
  background-color: $color-bg;
  border-bottom: 1px solid $color-border;
  height: 72px;
  display: flex;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 1000;

  &__container {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    height: 100%;

    @media (max-width: 1024px) {
      display: flex;
      justify-content: space-between;
    }
  }

  &__brand {
    display: flex;
    align-items: center;
    text-decoration: none;
    justify-self: start;
  }

  &__logo {
    height: 40px;
    width: auto;
    object-fit: contain;
  }

  &__links {
    list-style: none;
    display: flex;
    gap: $space-2xl;
    margin: 0;
    padding: 0;
    position: relative;
    justify-self: center;

    li {
      display: flex;
      align-items: center;
    }

    @media (max-width: 1024px) {
      display: none;
    }
  }

  &__link {
    text-decoration: none;
    color: $color-text-secondary; // Solid grey
    font-weight: 500;
    font-size: 0.9375rem;
    position: relative;
    transition: color $t-fast $ease;
    padding: $space-xs 0;

    &:hover {
      color: $color-text; // Darker on hover
    }

    &--active {
      color: $color-text;
      font-weight: 600;

      &::after {
        content: '';
        position: absolute;
        bottom: -2px;
        right: 0;
        left: 0;
        height: 2px;
        background-color: $color-brand;
        border-radius: 1px;
      }
    }
  }

  // Hamburger
  &__hamburger {
    display: none;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    gap: 6px;
    width: 44px;
    height: 44px;
    background: transparent;
    border: none;
    cursor: pointer;
    padding: 0;
    border-radius: $radius-md;
    transition: background-color $t-fast $ease;

    &:hover {
      background-color: $color-card; // Solid hover background
    }

    @media (max-width: 1024px) {
      display: flex;
    }
  }

  &__hamburger-line {
    width: 22px;
    height: 2px;
    background-color: $color-text;
    border-radius: 2px;
    transition: transform $t-base $ease;

    &--open {
      &:nth-child(1) {
        transform: translateY(8px) rotate(45deg);
      }
      &:nth-child(2) {
        transform: scale(0); // Scale instead of opacity
      }
      &:nth-child(3) {
        transform: translateY(-8px) rotate(-45deg);
      }
    }
  }

  // Mobile Menu
  &__mobile-menu {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background-color: $color-bg;
    border-bottom: 1px solid $color-border;
    border-radius: 0 0 $radius-md $radius-md;
    padding: $space-md 0;
    box-shadow: 0 4px 12px $color-shadow; // Solid shadow
    z-index: 999;
  }

  &__mobile-links {
    list-style: none;
    margin: 0;
    padding: 0 $container-padding;
    display: flex;
    flex-direction: column;
    gap: $space-xs;
  }

  &__mobile-link {
    display: block;
    padding: $space-sm $space-md;
    min-height: 44px;
    display: flex;
    align-items: center;
    text-decoration: none;
    color: $color-text-secondary;
    font-weight: 500;
    font-size: 1rem;
    border-radius: $radius-sm;
    transition: background-color $t-fast $ease;

    &:hover {
      background-color: $surface; // Solid hover
      color: $color-text;
    }
  }
}

// Vue Transition
.menu-enter-active,
.menu-leave-active {
  transition: transform $t-base $ease-out; // Transform only
}

.menu-enter-from,
.menu-leave-to {
  transform: translateY(-10px);
}
</style>
