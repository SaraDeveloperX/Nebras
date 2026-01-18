<script setup>
import Navbar from './components/Navbar.vue'
import Hero from './components/Hero.vue'
import HowItWorks from './components/HowItWorks.vue'
import Results from './components/Results.vue'
import Upload from './components/Upload.vue'
import Footer from './components/Footer.vue'
import { onMounted, nextTick } from 'vue'
import { initScrollMotion } from '@/utils/scrollMotion'

onMounted(async () => {
  await nextTick()
  initScrollMotion()
})
</script>

<template>
  <div class="app-layout">
    <Navbar />

    <main>
      <div id="overview">
        <Hero />
      </div>

      <div id="how">
        <HowItWorks />
      </div>

      <div id="results">
        <Results />
      </div>

      <div id="upload">
        <Upload />
      </div>
    </main>

    <Footer />
  </div>
</template>

<style scoped></style>
