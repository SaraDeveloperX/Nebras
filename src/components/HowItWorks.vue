<script setup>
const steps = [
  {
    id: 1,
    title: 'رفع البيانات المالية',
    text: 'تحميل الملفات المالية بصيغ شائعة مثل Excel أو CSV، بشكل مباشر وآمن.',
  },
  {
    id: 2,
    title: 'التحليل واستخلاص المؤشرات',
    text: 'تحليل الأداء المالي واستخلاص المؤشرات الرئيسية ذات التأثير المباشر على القرار.',
  },
  {
    id: 3,
    title: 'تقييم الوضع والمخاطر',
    text: 'تحديد الجوانب الحرجة والمخاطر المحتملة التي قد تؤثر على الاستقرار المالي.',
  },
  {
    id: 4,
    title: 'تقرير تنفيذي جاهز',
    text: 'تقرير واضح ومباشر يقدّم قراءة شاملة، موجّه للإدارة وقابل للاستخدام الفوري.',
  },
]
</script>

<template>
  <section class="how-it-works">
    <div class="container">
      <div class="how-it-works__header" data-motion="section">
        <h2 class="how-it-works__title">كيف يعمل النظام</h2>
        <p class="how-it-works__intro">
          تم تصميم النظام لتقديم قراءة تنفيذية دقيقة للبيانات المالية، تدعم القرار دون تعقيد أو تدخل
          يدوي.
        </p>
      </div>

      <div class="cards-grid">
        <div v-for="step in steps" :key="step.id" class="card" data-motion="item">
          <div class="card__number">{{ step.id }}.</div>
          <h3 class="card__title">{{ step.title }}</h3>
          <p class="card__text">{{ step.text }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.how-it-works {
  padding: $space-section 0;
  background-color: $color-bg;

  &__header {
    text-align: center;
    margin-bottom: $space-3xl;
  }

  &__title {
    color: $color-text;
    margin-bottom: $space-md;
  }

  &__intro {
    font-size: 1.0625rem;
    line-height: 1.7;
    color: $color-text-secondary; // Solid grey
    max-width: 560px;
    margin: 0 auto;
  }
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $space-lg;

  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
}

.card {
  position: relative;
  background-color: $surface;
  padding: 36px 40px;
  border-radius: 20px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  text-align: right;
  height: 100%;
  border: 1px solid $color-border; // Added solid border

  // Solid Box Shadow
  box-shadow: 0 4px 12px $color-shadow;

  transition:
    transform 400ms cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 400ms cubic-bezier(0.22, 1, 0.36, 1);

  // Removed ::before overlay to eliminate transparency

  // Executive Side Marker (RTL - Right Side)
  &::after {
    content: '';
    position: absolute;
    right: 0;
    top: 15%;
    width: 3px;
    height: 40%;
    background-color: $color-border-strong; // Solid color
    border-radius: 4px 0 0 4px;
    transition: height 400ms cubic-bezier(0.22, 1, 0.36, 1);
    z-index: 1;
  }

  // Content z-index fix
  & > * {
    position: relative;
    z-index: 2;
  }

  &:hover {
    transform: translateY(-4px) !important;
    box-shadow: 0 12px 24px $color-shadow; // Solid shadow

    &::after {
      height: 55%;
    }
  }

  &__number {
    font-size: 0.875rem;
    font-weight: 700;
    color: $color-text-muted; // Solid Muted
    margin-bottom: $space-lg;
  }

  &__title {
    font-size: 1.125rem;
    font-weight: 700;
    color: $color-text;
    margin-bottom: $space-md;
    line-height: 1.3;
  }

  &__text {
    font-size: 0.9375rem;
    line-height: 1.7;
    color: $color-text-secondary; // Solid Grey
    margin-bottom: 0;
    flex-grow: 1;
  }
}
</style>
