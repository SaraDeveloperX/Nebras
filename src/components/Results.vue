<script setup>
import reportImage from '../assets/report.jpg'

const items = [
  {
    title: 'ملخص تنفيذي',
    text: 'نظرة شاملة ومركّزة على الوضع المالي الحالي، توضح ما يحدث فعليًا وما يستحق انتباه الإدارة.',
  },
  {
    title: 'المؤشرات الرئيسية',
    text: 'عرض منظّم لأهم المؤشرات المالية ذات الأثر المباشر، يساعد على فهم الأداء وتفسير نتائجه.',
  },
  {
    title: 'المخاطر المحتملة',
    text: 'تحديد الجوانب التي قد تؤثر في الاستقرار المالي، مع توضيح مصادرها وتأثيرها المتوقع.',
  },
  {
    title: 'توصيات قابلة للتنفيذ',
    text: 'إجراءات عملية مرتّبة حسب الأولوية، مصممة لدعم القرار وتحسين الأداء المالي.',
  },
]
</script>

<template>
  <section class="results">
    <div class="container results__container">
      <!-- Text Content -->
      <div class="results__content" data-motion="section">
        <h2 class="results__title">ماذا ستحصل عليه</h2>

        <ul class="results__list">
          <li v-for="(item, index) in items" :key="index" class="results__item" data-motion="item">
            <span class="results__bullet" aria-hidden="true"></span>
            <div class="results__item-content">
              <h3 class="results__item-title">{{ item.title }}</h3>
              <p class="results__item-text">{{ item.text }}</p>
            </div>
          </li>
        </ul>
      </div>

      <!-- Illustration -->
      <div class="results__visual" data-motion="section">
        <img :src="reportImage" alt="معاينة التقرير التنفيذي" class="results__image" />
      </div>
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.results {
  padding: $space-section 0;
  background-color: $color-bg;

  &__container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: $space-3xl;
    align-items: center;

    @media (max-width: 900px) {
      display: flex;
      flex-direction: column;
      gap: $space-2xl;
      text-align: center;
    }
  }

  &__content {
    grid-column: 2;
    grid-row: 1;
    text-align: right;
    // Reveal class handles animation

    @media (max-width: 900px) {
      order: 2; // Text below illustration
      text-align: right; // Restore reading direction
      width: 100%;
      margin-top: 0; // Reset any potential margins
    }
  }

  &__visual {
    grid-column: 1;
    grid-row: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    // Reveal class handles animation

    @media (max-width: 900px) {
      order: 1; // Illustration on top
      width: 100%;
      max-width: 420px; // Constraint width
      margin: 0 auto $space-xl auto; // Center and add bottom margin
      // Remove transform overrides or resets as .reveal handles it now
      position: relative; // Ensure no absolute positioning leaks
      z-index: 1;
    }
  }

  &__image {
    width: 100%;
    max-width: 520px;
    height: auto;
    display: block;

    @media (max-width: 900px) {
      max-width: 420px;
    }
  }

  &__title {
    color: $color-text;
    margin-bottom: $space-xl;
  }

  &__list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: $space-lg;
  }

  &__item {
    display: flex;
    align-items: flex-start;
    gap: $space-sm;
    // Reveal handles animation

    @media (max-width: 768px) {
      // Logic handled by global .reveal media query
    }
  }

  &__bullet {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: $color-text-muted; // Solid muted
    flex-shrink: 0;
    margin-top: 10px;
  }

  &__item-title {
    font-size: 1.0625rem;
    font-weight: 700;
    color: $color-text;
    margin-bottom: $space-xs;
  }

  &__item-text {
    font-size: 0.9375rem;
    line-height: 1.65;
    color: $color-text-secondary; // Solid secondary
    margin-bottom: 0;
    line-height: 1.75;
  }
}
</style>
