<script setup></script>

<template>
  <footer class="footer">
    <div class="footer__container container" data-motion="section">
      <img src="@/assets/logo.png" alt="نبراس" class="footer__logo" />
      <p class="footer__copyright">جميع الحقوق محفوظة. © 2026</p>
    </div>
  </footer>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.footer {
  position: relative;
  width: 100%;
  margin-top: $space-section;
  padding: $space-xl 0;
  border-top: 1px solid $color-border; // Solid border
  background-color: $surface; // Solid background
  overflow: hidden;

  // Removed __bg layer with backdrop-filter

  &__container {
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: $space-md;
    opacity: 1;
  }

  &__logo {
    height: 32px;
    width: auto;
    object-fit: contain;
    opacity: 1;
    filter: none;
  }

  &__copyright {
    font-size: 0.875rem;
    color: $color-text-secondary; // Solid secondary text
    text-align: center;
    margin-bottom: 0;
    opacity: 1;
  }
}
</style>
