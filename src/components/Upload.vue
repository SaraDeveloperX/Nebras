<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { BASE_API_URL } from '../config/api'

const fileInputRef = ref(null)
const file = ref(null)
const concern = ref('')
const isAnalyzing = ref(false)
const error = ref(null)
const analysisResults = ref(null)

const isDemo = ref(false)

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileChange = (event) => {
  const selected = event.target.files[0]
  if (selected) {
    file.value = selected
    error.value = null // clear previous errors
    isDemo.value = false
  }
}

const generateDemoCSV = () => {
  const rows = [
    'date,amount,type,category',
    '2024-01-02,5000,Income,Sales',
    '2024-01-05,-1500,Expense,Rent',
    '2024-01-07,-200,Expense,Utilities',
    '2024-01-10,3000,Income,Consulting',
    '2024-01-15,-500,Expense,Marketing',
    '2024-01-20,-2000,Expense,Salaries',
    '2024-01-25,-300,Expense,Software',
    '2024-01-28,1500,Income,Sales',
    '2024-02-01,6000,Income,Sales',
    '2024-02-05,-1500,Expense,Rent',
    '2024-02-07,-250,Expense,Utilities',
    '2024-02-10,4000,Income,Consulting',
    '2024-02-12,-800,Expense,Marketing',
    '2024-02-15,-2000,Expense,Salaries',
    '2024-02-20,-100,Expense,Office',
    '2024-02-22,2000,Income,Sales',
    '2024-02-25,-400,Expense,Software',
    '2024-02-28,500,Income,Other',
    '2024-03-01,7500,Income,Sales',
    '2024-03-05,-1500,Expense,Rent',
    '2024-03-07,-220,Expense,Utilities',
    '2024-03-10,5000,Income,Consulting',
    '2024-03-12,-1200,Expense,Marketing',
    '2024-03-15,-2200,Expense,Salaries',
    '2024-03-18,-500,Expense,Travel',
    '2024-03-20,3000,Income,Sales',
    '2024-03-25,-400,Expense,Software',
    '2024-03-28,1000,Income,Other',
    '2024-03-30,-100,Expense,Bank Fees',
  ]
  return rows.join('\n')
}

const useDemoData = () => {
  const csvContent = generateDemoCSV()
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const demoFile = new File([blob], 'demo.csv', { type: 'text/csv' })

  file.value = demoFile
  isDemo.value = true
  error.value = null

  submitAnalysis()
}

const handleMainButtonClick = () => {
  if (!file.value) {
    triggerFileInput()
  } else {
    submitAnalysis()
  }
}

const submitAnalysis = async () => {
  if (!file.value) return

  isAnalyzing.value = true
  error.value = null
  analysisResults.value = null
  startProgress()

  const formData = new FormData()
  formData.append('file', file.value)
  if (concern.value) {
    formData.append('concern', concern.value)
  }
  // isDemo is already a ref, we can check its value
  if (isDemo.value) {
    formData.append('is_demo', '1')
  }

  try {
    const response = await fetch(`${BASE_API_URL}/api/analyze`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}))
      const detail = errData.detail || 'فشل التحليل'
      const status = response.status
      // Throw with status for better handling
      const error = new Error(detail)
      error.status = status
      throw error
    }

    const data = await response.json()
    // Ensure we reached step 4 before showing results
    progressStep.value = 4
    // Small delay to let user see step 4 completion
    setTimeout(() => {
      analysisResults.value = data
      isSummaryExpanded.value = false // Reset expansion logic
      stopProgress()
      isAnalyzing.value = false
    }, 500)
  } catch (err) {
    console.error('Analysis error:', err)
    error.value =
      typeof err.message === 'string' && err.message.length < 200
        ? err.message
        : 'حدث خطأ أثناء معالجة الملف.'
    stopProgress(true) // stop with error

    // Determine Error Details
    let url = `${BASE_API_URL}/api/analyze`

    errorDetails.value = {
      message: error.value,
      originalError: err.message || err.toString(),
      url: url,
      status: err.status || null,
    }
  }
}

const retryAnalysis = () => {
  if (!file.value && !isDemo.value) return
  error.value = null
  errorDetails.value = null
  submitAnalysis()
}

// Error Mapping Logic
const errorDetails = ref(null)
const isDev = import.meta.env.DEV

const errorTitle = computed(() => {
  const status = errorDetails.value?.status
  // No title for 400 (invalid file) or 429 (rate limit)
  if (status === 400 || status === 429) {
    return ''
  }
  return 'تعذر إكمال التحليل'
})

const errorMessageBody = computed(() => {
  const status = errorDetails.value?.status

  // For 400 and 429, show ONLY the backend message (no custom text)
  if (status === 400 || status === 429) {
    return errorDetails.value?.message || 'حدث خطأ غير متوقع.'
  }

  // 500 / 502
  const msg = errorDetails.value?.originalError || ''
  if (msg.includes('500') || msg.includes('502') || msg.includes('Internal Server Error')) {
    return 'تعذر إكمال التحليل حالياً. تحقق من تشغيل السيرفر ثم أعد المحاولة.'
  }

  // Network (Failed to fetch)
  if (msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
    return 'تعذر الاتصال بالسيرفر. تأكد من اتصالك بالإنترنت أو إعدادات الشبكة (CORS/Firewall).'
  }

  // Other errors (Backend message)
  if (errorDetails.value?.message) {
    return errorDetails.value.message
  }

  return 'حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.'
})

const isLimitError = computed(() => {
  const status = errorDetails.value?.status
  // Hide retry button for both 400 (invalid file) and 429 (rate limit)
  return status === 400 || status === 429
})

// Progress Logic
const progressStep = ref(0)
const progressTimers = []
const progressSteps = [
  {
    title: 'استلام الملف',
    desc: 'التحقق من البيانات وتجهيزها للتحليل',
  },
  {
    title: 'تحليل المؤشرات',
    desc: 'احتساب KPIs واستخلاص الملاحظات',
  },
  {
    title: 'رصد المخاطر',
    desc: 'تحديد الأنماط غير الطبيعية ونقاط الانتباه',
  },
  {
    title: 'إعداد التقرير',
    desc: 'تجهيز التقرير التنفيذي بصيغة PDF',
  },
]

const startProgress = () => {
  progressStep.value = 1
  progressTimers.forEach(clearTimeout)
  progressTimers.length = 0

  // Simulate timings
  progressTimers.push(
    setTimeout(() => {
      if (isAnalyzing.value) progressStep.value = 2
    }, 400),
  )
  progressTimers.push(
    setTimeout(() => {
      if (isAnalyzing.value) progressStep.value = 3
    }, 900),
  )
  progressTimers.push(
    setTimeout(() => {
      if (isAnalyzing.value) progressStep.value = 4
    }, 1400),
  )
}

const stopProgress = (hasError = false) => {
  progressTimers.forEach(clearTimeout)
  progressTimers.length = 0
  if (hasError) {
    isAnalyzing.value = false
    // Keep current step but maybe mark as error in UI if needed,
    // strictly spec says "keep current step active + mark status 'Unable to complete'"
    // check UI implementation for this.
  } else {
    progressStep.value = 0 // Reset or keep 4? Spec says "On success: Step4 done, show results".
    // If we show results, usually we hide progress.
    // Let's hide progress when results are shown (v-if on isAnalyzing).
  }
}

const pdfUrl = computed(() => {
  if (!analysisResults.value?.report_pdf_url) return '#'
  const url = analysisResults.value.report_pdf_url
  if (url.startsWith('http')) return url
  return `${BASE_API_URL}${url.startsWith('/') ? '' : '/'}${url}`
})

const executiveKPIs = computed(() => {
  if (!analysisResults.value?.kpis) return []
  const targetNames = ['إجمالي الإيرادات', 'إجمالي المصروفات', 'صافي الربح']
  return analysisResults.value.kpis.filter((k) => targetNames.includes(k.name))
})

const isSummaryExpanded = ref(false)
const isTruncated = ref(false)
const summaryTextRef = ref(null)

const checkTruncation = async () => {
  await nextTick()
  if (summaryTextRef.value) {
    // Check if scrollHeight is significantly larger than clientHeight
    // Use a small buffer (e.g. 2px) to avoid false positives due to rounding
    isTruncated.value = summaryTextRef.value.scrollHeight > summaryTextRef.value.clientHeight + 2
  }
}

watch(analysisResults, () => {
  if (analysisResults.value) {
    checkTruncation()
  }
})
</script>

<template>
  <section id="upload" class="upload">
    <div class="container upload__container">
      <div class="upload__content">
        <h2 class="upload__title" data-motion="section">هل بياناتك المالية جاهزة للتحليل؟</h2>
        <p class="upload__description" data-motion="section">
          ارفع ملفاتك المالية الآن واحصل على تقريرك التنفيذي فورًا.
        </p>

        <div class="upload__actions" data-motion="item">
          <input
            type="file"
            ref="fileInputRef"
            accept=".xlsx,.xls,.csv"
            class="upload__file-input"
            @change="handleFileChange"
          />

          <button
            class="upload__btn upload__btn--primary"
            @click="handleMainButtonClick"
            :disabled="isAnalyzing"
          >
            <span v-if="isAnalyzing">جارٍ التحليل...</span>
            <span v-else-if="file">ابـدأ التحليل ({{ file.name }})</span>
            <span v-else>رفع الملف</span>
          </button>

          <button
            class="upload__btn upload__btn--secondary"
            :disabled="isAnalyzing"
            @click="useDemoData"
          >
            استخدام بيانات تجريبية
          </button>
        </div>

        <!-- Progress Tracker -->
        <div v-if="isAnalyzing" class="upload__progress">
          <div
            v-for="(step, index) in progressSteps"
            :key="index"
            class="upload__progress-step"
            :class="{
              active: index + 1 === progressStep,
              done: index + 1 < progressStep,
              error: error && index + 1 === progressStep,
            }"
          >
            <!-- 1. Icon on Right (Start in RTL) -->
            <div class="step-icon-wrapper">
              <div
                class="step-icon"
                :class="{
                  'is-active': index + 1 === progressStep,
                  'is-done': index + 1 < progressStep,
                  'is-pending': index + 1 > progressStep,
                }"
              >
                <!-- DONE STATE -->
                <svg
                  v-if="index + 1 < progressStep"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M20 6L9 17L4 12"
                    stroke="white"
                    stroke-width="3"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>

                <!-- ERROR STATE -->
                <span v-else-if="error && index + 1 === progressStep">✕</span>

                <!-- ACTIVE STATE (Spinner) -->
                <div v-else-if="index + 1 === progressStep" class="step-spinner"></div>

                <!-- PENDING STATE (Empty) -->
                <span v-else></span>
              </div>
            </div>

            <!-- 2. Text Content -->
            <div class="step-content">
              <span class="step-title">{{ step.title }}</span>
              <!-- Error Message if applicable -->
              <span v-if="error && index + 1 === progressStep" class="error-status">
                تعذر الإكمال
              </span>
              <!-- Description -->
              <p class="step-desc">{{ step.desc }}</p>
            </div>
          </div>

          <!-- New Output Block: Visible only during analysis -->
          <div class="upload__outputs">
            <h4 class="upload__outputs-title">عرض النتائج</h4>
            <ul class="upload__outputs-list">
              <li>داخل التطبيق: عرض سريع وتفاعلي للنتائج (KPIs، المخاطر، التوصيات).</li>
              <li>بصيغة PDF: تقرير تنفيذي رسمي للمشاركة والإرسال والأرشفة أو العرض على الإدارة.</li>
            </ul>
          </div>
        </div>

        <!-- Premium Error Card -->
        <div v-if="error" class="upload__error-card" data-motion="item">
          <div class="error-icon-wrapper">
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M12 9V14"
                stroke="#D32F2F"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
              <path
                d="M12 21.41L13.41 20M12 2.59L10.59 4"
                stroke="#D32F2F"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                opacity="0"
              />
              <circle cx="12" cy="12" r="10" stroke="#D32F2F" stroke-width="2" />
              <path
                d="M12 17H12.01"
                stroke="#D32F2F"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </div>
          <div class="error-content">
            <h4 v-if="errorTitle" class="error-title">{{ errorTitle }}</h4>
            <p class="error-body">{{ errorMessageBody }}</p>

            <!-- Debug Info (DEV ONLY) -->
            <div v-if="isDev && errorDetails && !isLimitError" class="error-debug">
              <small dir="ltr">API: {{ errorDetails.url }}</small
              ><br />
              <small dir="ltr">Err: {{ errorDetails.originalError }}</small>
            </div>

            <button v-if="!isLimitError" class="error-retry-btn" @click="retryAnalysis">
              إعادة المحاولة
            </button>
          </div>
        </div>
      </div>

      <div class="upload__question" data-motion="item">
        <label class="upload__question-label"> ما أكبر قلق مالي لديك هذا الشهر؟ </label>
        <input
          v-model="concern"
          type="text"
          class="upload__question-input"
          placeholder="مثال: انخفاض السيولة، تذبذب الربحية، ارتفاع الالتزامات"
          :disabled="isAnalyzing"
        />
        <p class="upload__question-helper">يساعدنا على توجيه التحليل نحو أهم ما يهمك.</p>
      </div>
    </div>

    <!-- Results Panel: Executive Preview -->
    <div v-if="analysisResults" class="container results__container">
      <!-- 1. Header -->
      <div class="results__header">
        <h3 class="results__title">
          نتائج التحليل
          <span v-if="isDemo" class="results__badge">بيانات تجريبية</span>
        </h3>
      </div>

      <!-- 2. Executive Summary Card -->
      <div class="results__summary-card" data-motion="item">
        <h4 class="summary-label">الملخص التنفيذي</h4>
        <div class="summary-content-wrapper">
          <p
            ref="summaryTextRef"
            class="summary-text"
            :class="{ 'summary-text--expanded': isSummaryExpanded }"
          >
            {{ analysisResults.summary }}
          </p>
        </div>

        <button
          v-if="isTruncated"
          class="summary-toggle"
          @click="isSummaryExpanded = !isSummaryExpanded"
        >
          {{ isSummaryExpanded ? 'عرض أقل' : 'عرض المزيد' }}
        </button>
      </div>

      <!-- 3. Key Highlights (3 Cards Only) -->
      <div class="results__kpis">
        <div
          v-for="(kpi, idx) in executiveKPIs"
          :key="idx"
          class="results__kpi-card"
          data-motion="item"
        >
          <!-- Icon based on name mapping -->
          <div class="kpi-icon-wrapper">
            <div v-if="kpi.name.includes('الإيرادات')" class="kpi-icon revenue-icon">
              <!-- Simple Up Arrow / Chart -->
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <line x1="12" y1="19" x2="12" y2="5"></line>
                <polyline points="5 12 12 5 19 12"></polyline>
              </svg>
            </div>
            <div v-else-if="kpi.name.includes('المصروفات')" class="kpi-icon expense-icon">
              <!-- Down Arrow -->
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <polyline points="19 12 12 19 5 12"></polyline>
              </svg>
            </div>
            <div v-else class="kpi-icon profit-icon">
              <!-- Star / Check -->
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <polygon
                  points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"
                ></polygon>
              </svg>
            </div>
          </div>

          <div class="kpi-content">
            <span class="results__kpi-name">{{ kpi.name }}</span>
            <strong class="results__kpi-value">{{ kpi.value }}</strong>

            <div class="kpi-meta">
              <span
                class="results__kpi-delta"
                :class="{ positive: kpi.delta.includes('+'), negative: kpi.delta.includes('-') }"
              >
                {{ kpi.delta }}
              </span>
            </div>

            <p v-if="kpi.insight" class="results__kpi-insight">
              {{ kpi.insight }}
            </p>
          </div>
        </div>
      </div>

      <!-- 4. Call to Action -->
      <div class="results__actions" data-motion="item">
        <a
          :href="pdfUrl"
          target="_blank"
          class="upload__btn upload__btn--primary results__download-btn"
        >
          تحميل التقرير التنفيذي PDF
        </a>
        <p class="results__helper-text">التفاصيل الكاملة، المخاطر، والتوصيات داخل التقرير</p>
      </div>
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '../styles/variables' as *;

.upload {
  padding: $space-section 0;
  background-color: $color-bg;

  &__container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: $space-3xl;
    align-items: start;

    @media (max-width: 900px) {
      grid-template-columns: 1fr;
      gap: $space-2xl;
    }
  }

  &__content {
    text-align: right;
  }

  &__title {
    color: $color-text;
    margin-bottom: $space-md;
  }

  &__description {
    font-size: 1.0625rem;
    line-height: 1.7;
    color: rgba($color-text, 0.7);
    margin-bottom: $space-xl;
    max-width: 480px;
  }

  &__actions {
    display: flex;
    flex-wrap: wrap;
    gap: $space-md;
  }

  &__file-input {
    display: none;
  }

  &__btn {
    height: 44px;
    padding: 0 $space-xl;
    border-radius: $radius-md;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all $t-fast $ease;
    white-space: nowrap;

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    &--primary {
      background-color: $surface;
      color: $color-text;
      border: 1px solid rgba($color-text, 0.1);

      &:hover:not(:disabled) {
        background-color: darken($surface, 5%);
        border-color: rgba($color-text, 0.2);
        transform: translateY(-1px);
      }
    }

    &--secondary {
      background-color: transparent;
      color: $color-text;
      border: 1px solid rgba($color-text, 0.15);

      &:hover:not(:disabled) {
        background-color: rgba($surface, 0.5);
        border-color: rgba($color-text, 0.25);
        transform: translateY(-1px);
      }
    }
  }

  &__progress {
    margin-top: $space-xl;
    max-width: 520px;
    margin-left: auto;
    margin-right: auto;
    text-align: right;
    background-color: #edeeef; // CHANGED: Subtle premium background
    border-radius: 18px;
    padding: 18px 20px;
    // Removed border if not needed by spec (user said "subtle background", didn't ask for border, but subtle border is okay. I will remove it to be cleaner as per "Card" look usually implies bg vs bg).
    // Actually, user spec: "Progress must be inside ONE card container with subtle background (#edeeef) and rounded corners."
    // No border mentioned. I'll remove the border to be safe/cleaner or keep it very subtle.
    // I'll keep the shadow or nothing? User didn't ask for shadow.
    border: none;
  }

  &__progress-step {
    --stepIconSize: 32px; // CHANGED: 32px max

    display: flex;
    align-items: flex-start; // Align start for title/subtitle flow
    gap: 12px;
    padding: 14px 6px;
    border-bottom: 1px solid rgba(56, 62, 80, 0.1);

    &:first-child {
      padding-top: 14px; // Consistent padding
    }

    &:last-child {
      border-bottom: none;
      padding-bottom: 14px;
    }

    .step-icon-wrapper {
      flex-shrink: 0;
      padding-top: 2px; // slight alignment with text title cap-height
    }

    .step-icon {
      width: var(--stepIconSize);
      height: var(--stepIconSize);
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      transition: all 0.3s ease;
      box-sizing: border-box;

      // PENDING STATE
      &.is-pending {
        background-color: transparent;
        border: 2px solid rgba(56, 62, 80, 0.2); // Ring only
        color: transparent;
      }

      // DONE STATE
      &.is-done {
        background-color: #383e50; // Filled
        border: none; // No border
        color: #ffffff;
      }

      // ACTIVE STATE
      &.is-active {
        background-color: transparent;
        border: 2px solid rgba(56, 62, 80, 0.25); // Outer Ring
        color: transparent;
        position: relative; // For centering spinner
        padding: 0;
      }
    }

    // SPINNER for Active State
    .step-spinner {
      width: 18px; // CHANGED: 18px
      height: 18px;
      border-radius: 50%;
      border: 2px solid rgba(30, 30, 30, 0); // Transparent track
      border-top-color: #383e50; // Active Arc
      border-right-color: #383e50; // Extra visible arc for better spinner visibility
      animation: spin 1s linear infinite; // 1s linear
      box-sizing: border-box;
    }

    // CONTENT
    .step-content {
      flex: 1;
      text-align: right;
    }

    .step-title {
      display: block;
      font-size: 0.9375rem;
      font-weight: 700;
      color: #383e50;
      margin-bottom: 2px; // Tight spacing
      line-height: 1.3;
    }

    .step-desc {
      display: block;
      font-size: 0.8125rem;
      color: rgba(56, 62, 80, 0.65);
      margin: 0;
      line-height: 1.4;
    }

    .error-status {
      color: #d32f2f;
      font-weight: 600;
      font-size: 0.8125rem;
      margin-right: 4px;
    }
  }

  &__outputs {
    margin-top: 28px;
    padding-top: 24px;
    border-top: 1px solid rgba(56, 62, 80, 0.1);
    text-align: right;
    animation: fadeIn 0.4s ease-out;

    &-title {
      font-size: 16px; // "Title bold, 16px"
      font-weight: 700;
      color: #383e50;
      margin-bottom: 12px;
    }

    &-list {
      list-style: none;
      padding: 0;
      margin: 0;

      li {
        position: relative;
        padding-right: 14px;
        margin-bottom: 8px;
        font-size: 14px; // "Bullets: 14px"
        color: rgba(56, 62, 80, 0.7);
        line-height: 1.6;

        &::before {
          content: '•';
          position: absolute;
          right: 0;
          color: #383e50;
          font-weight: bold;
        }
      }
    }
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
  // Premium Error Card
  &__error-card {
    margin-top: $space-xl;
    background-color: #fdf2f2; // Light Red Bg
    border: 1px solid #fecdd2;
    border-radius: 18px;
    padding: 20px;
    text-align: right;
    display: flex;
    align-items: flex-start;
    gap: 16px;
    max-width: 520px;
    margin-left: auto;
    margin-right: auto;

    .error-icon-wrapper {
      flex-shrink: 0;
      margin-top: 2px;
    }

    .error-content {
      flex: 1;
    }

    .error-title {
      color: #b71c1c; // Dark Red
      font-weight: 700;
      font-size: 1rem;
      margin-bottom: 8px;
    }

    .error-body {
      color: #c62828;
      font-size: 0.9375rem;
      line-height: 1.5;
      margin-bottom: 16px;
    }

    .error-helper {
      font-size: 0.85rem;
      color: rgba(183, 28, 28, 0.7);
      margin-top: -12px;
      margin-bottom: 16px;
    }

    .error-debug {
      background: rgba(0, 0, 0, 0.05);
      padding: 8px;
      border-radius: 6px;
      margin-bottom: 12px;
      font-family: monospace;
      font-size: 11px;
      color: #333;
      text-align: left;
    }

    .error-retry-btn {
      background-color: #ffffff;
      border: 1px solid #e57373;
      color: #c62828;
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 0.875rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;

      &:hover {
        background-color: #ffebee;
      }
    }
  }

  // Illustration (Upload Area) container styling
  &__illustration-container {
    margin-bottom: 24px;
    // Removed box-shadow with opacity
    filter: none;

    &::before {
      content: none; // Remove glow
    }

    &::after {
      content: none; // Remove marker
    }
  }

  &__illustration-wrapper {
    position: relative;
    z-index: 1; // Strict
  }

  &__question {
    margin-top: 40px;
    width: 100%;
    max-width: 500px;
    margin-left: auto;
    margin-right: auto;
  }

  &__question-label {
    display: block;
    font-size: 1rem;
    font-weight: 600;
    color: $color-text;
    margin-bottom: $space-sm;
  }

  &__question-input {
    width: 100%;
    height: 44px;
    padding: 0 $space-md;
    border: 1px solid $color-border; // Solid border
    border-radius: $radius-md;
    font-size: 0.9375rem;
    color: $color-text;
    background-color: #ffffff;
    text-align: right;
    transition: border-color $t-fast $ease;

    &:focus {
      outline: 2px solid $color-border-strong;
      border-color: $color-text;
    }

    &:disabled {
      background-color: $surface;
      cursor: not-allowed;
    }
  }

  &__question-helper {
    font-size: 0.875rem;
    color: $color-text-muted;
    margin-top: $space-xs;
  }
}

/* Results Styles */
.results {
  -webkit-font-smoothing: antialiased; // Ensure crisp text on Safari
  -moz-osx-font-smoothing: grayscale;

  &__container {
    margin-top: 60px;
    padding-top: 40px;
    border-top: 1px solid #ebeced; // Solid equivalent of rgba($color-text, 0.06)
    text-align: right;
    animation: fadeIn 0.6s ease-out;
  }

  &__header {
    margin-bottom: 32px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  &__title {
    font-size: 1.5rem;
    font-weight: 700;
    color: $color-text;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  &__badge {
    font-size: 0.75rem;
    background: #e0f2f1;
    color: #00695c;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: 600;
    // border: 1px solid rgba(0, 105, 92, 0.15); No border for cleaner look
  }

  // Executive Summary Card
  &__summary-card {
    background: white;
    padding: 32px;
    border-radius: 16px;
    // Soft shadow instead of blur
    box-shadow: 0 2px 12px #e5e5e5; // Solid shadow approximation for "no transparency" feel, technically hex shadow is solid color but box-shadow spreads it. Let's keep distinct.
    border: 1px solid #ebeced; // Solid equivalent of rgba($color-text, 0.04)
    margin-bottom: 40px;
    backdrop-filter: none; // Explicitly remove any potential blur
    -webkit-backdrop-filter: none;

    .summary-label {
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #878b96; // Solid equivalent of rgba($color-text, 0.5)
      margin-bottom: 12px;
      font-weight: 700;
    }

    .summary-text {
      font-size: 1.1rem;
      line-height: 1.7;
      color: $color-text;
      font-weight: 500;
      opacity: 1;

      // Truncation Logic
      display: -webkit-box;
      -webkit-box-orient: vertical;
      overflow: hidden;
      -webkit-line-clamp: 3; // Desktop max lines

      @media (max-width: 600px) {
        -webkit-line-clamp: 2; // Mobile max lines
      }

      &--expanded {
        -webkit-line-clamp: unset;
        display: block;
      }
    }

    .summary-toggle {
      background: none;
      border: none;
      color: $color-brand; // Solid brand color
      font-weight: 600;
      font-size: 0.9rem;
      cursor: pointer;
      padding: 0;
      margin-top: 12px;
      font-family: inherit;
      display: inline-block;

      &:hover {
        text-decoration: underline; // Subtle interaction
      }
    }
  }

  &__kpis {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 24px;
    margin-bottom: 48px;
  }

  &__kpi-card {
    background: white; // transparent or white? White for cards.
    // Spec: "Minimal card, premium spacing"
    padding: 24px;
    border-radius: 16px;
    border: 1px solid #ebeced; // Solid
    display: flex;
    flex-direction: column; // Vertical layout inside card
    align-items: flex-start; // RTL Right aligned = flex-start
    gap: 16px;
    transition:
      transform 0.3s ease,
      box-shadow 0.3s ease;
    // Ensure no blur
    backdrop-filter: none;
    -webkit-backdrop-filter: none;
    filter: none;

    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 16px #e0e0e0; // Solid shadow color
    }

    .kpi-icon-wrapper {
      margin-bottom: 8px;
    }

    .kpi-icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;

      // Solid background colors (light tints)
      &.revenue-icon {
        background: #e8f5e9;
        color: #2e7d32;
      }
      &.expense-icon {
        background: #ffebee;
        color: #c62828;
      }
      &.profit-icon {
        background: #fff8e1;
        color: #ff8f00;
      }
    }

    .kpi-content {
      width: 100%;
    }

    .results__kpi-name {
      font-size: 0.9rem;
      color: #878b96; // Solid grey
      display: block;
      margin-bottom: 4px;
      opacity: 1;
    }

    .results__kpi-value {
      font-size: 1.75rem;
      color: $color-text;
      font-weight: 700;
      line-height: 1.2;
      display: block;
      margin-bottom: 8px;
      opacity: 1;
    }

    .kpi-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
    }

    .results__kpi-delta {
      font-size: 0.85rem;
      font-weight: 600;
      padding: 2px 6px;
      border-radius: 4px;
      opacity: 1;

      &.positive {
        color: #2e7d32;
        background: #e8f5e9; // Solid
      }
      &.negative {
        color: #c62828;
        background: #ffebee; // Solid
      }
    }

    .results__kpi-insight {
      font-size: 0.85rem;
      color: #5c606e; // Solid darker grey for readability
      line-height: 1.4;
      border-top: 1px solid #ebeced; // Solid
      padding-top: 12px;
      width: 100%;
      opacity: 1;
    }
  }

  &__actions {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    margin-top: 24px;
  }

  &__download-btn {
    min-width: 280px;
    height: 52px;
    font-size: 1.05rem;
    box-shadow: 0 4px 12px #d0d0d0; // Solid shadow
    text-decoration: none;

    &:hover {
      box-shadow: 0 6px 16px #c0c0c0;
    }
  }

  &__helper-text {
    font-size: 0.85rem;
    color: #878b96; // Solid
    opacity: 1;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
