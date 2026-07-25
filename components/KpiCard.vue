<script setup lang="ts">
defineProps<{
  label: string
  value: string
  hint?: string
  accent?: 'good' | 'warning' | 'critical' | null
}>()
</script>

<template>
  <div class="panel kpi">
    <div class="kpi-label">{{ label }}</div>
    <div class="kpi-value" :class="accent ?? ''">{{ value }}</div>
    <div v-if="hint" class="kpi-hint">{{ hint }}</div>
  </div>
</template>

<style scoped>
.kpi { margin: 0; padding: 18px 20px; }
.kpi-label {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin-bottom: 8px;
}
.kpi-value {
  font-size: 1.9rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1;
}
.kpi-value.good { color: #0a7a0a; }
.kpi-value.warning { color: #8a5d00; }
.kpi-value.critical { color: #a72a2a; }
.kpi-hint {
  margin-top: 8px;
  font-size: 0.78rem;
  color: var(--text-muted);
}
</style>
