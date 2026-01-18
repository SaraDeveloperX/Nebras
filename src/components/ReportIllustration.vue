<script setup></script>

<template>
  <div class="illustration-wrapper">
    <svg
      viewBox="0 0 220 280"
      class="report-illustration"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="تقرير تنفيذي"
    >
      <!-- Paper with subtle tilt -->
      <g transform="rotate(-4, 110, 140)">
        <!-- Paper sheet -->
        <rect
          x="25"
          y="15"
          width="170"
          height="230"
          rx="6"
          fill="#FFFFFF"
          stroke="#e1e2e5"
          stroke-width="1.5"
        />

        <!-- Header area -->
        <rect x="45" y="40" width="90" height="10" rx="3" fill="#e7e8ea" />
        <rect x="155" y="38" width="20" height="14" rx="3" fill="#eff0f1" />

        <!-- Divider -->
        <line x1="45" y1="68" x2="175" y2="68" stroke="#eff0f1" stroke-width="1" />

        <!-- Content block 1 -->
        <rect x="45" y="85" width="130" height="7" rx="2" fill="#eff0f1" />
        <rect x="45" y="100" width="110" height="7" rx="2" fill="#eff0f1" />
        <rect x="45" y="115" width="120" height="7" rx="2" fill="#eff0f1" />

        <!-- Section header -->
        <rect x="45" y="142" width="70" height="8" rx="2" fill="#e1e2e5" />

        <!-- Content block 2 -->
        <rect x="45" y="165" width="130" height="7" rx="2" fill="#eff0f1" />
        <rect x="45" y="180" width="100" height="7" rx="2" fill="#eff0f1" />
        <rect x="45" y="195" width="115" height="7" rx="2" fill="#eff0f1" />

        <!-- Footer -->
        <rect x="45" y="220" width="55" height="6" rx="2" fill="#f3f4f5" />
      </g>
    </svg>
  </div>
</template>

<style scoped>
.illustration-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

.report-illustration {
  width: 100%;
  max-width: 300px;
  height: auto;
  display: block;
}
</style>
