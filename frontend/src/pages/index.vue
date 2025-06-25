<template>
  <v-container class="fill-height d-flex flex-column align-center justify-center" 
      style="background: linear-gradient(135deg, #f8bbd0 0%, #b2ebf2 100%); min-height: 100vh; max-width: none;">
    <v-card class="pa-8" max-width="500" elevation="12"
      style="border-radius: 32px; background: linear-gradient(135deg, #fffde7 0%, #fce4ec 100%);">
      <v-row class="mb-6" align="center" justify="center">
        <v-icon color="pink lighten-2" size="48">mdi-heart-multiple</v-icon>
        <span class="text-h3 font-weight-bold ml-4" style="color: #ec407a; letter-spacing: 2px;">Electro Cupid</span>
      </v-row>
      <v-form @submit.prevent="onSubmit">
        <v-file-input
          v-model="bomFile"
          label="Upload Bill of Materials (PDF, CSV, XLS, etc.)"
          prepend-icon="mdi-upload"
          show-size
          class="mb-4"
          color="cyan lighten-2"
          variant="outlined"
          :disabled="readonly"
        />
        <v-text-field
          v-model="context"
          label="Environment / Usage Context"
          prepend-icon="mdi-earth"
          class="mb-4"
          color="purple lighten-2"
          variant="outlined"
          :readonly="readonly"
        />
        <v-text-field
          v-model="quantity"
          label="Quantity to Produce"
          prepend-icon="mdi-counter"
          type="number"
          min="1"
          color="deep-orange lighten-2"
          variant="outlined"
          :readonly="readonly"
        />
        <v-btn
          class="mt-6"
          color="pink accent-2"
          size="large"
          block
          elevation="6"
          type="submit"
          :loading="loading"
          :disabled="loading || readonly"
        >
          Submit
          <v-icon end>mdi-arrow-right</v-icon>
        </v-btn>
      </v-form>
      <div v-if="pollError" class="mt-4 text-error">{{ pollError }}</div>
      <div v-if="ready" class="mt-6 d-flex flex-column align-center">
        <v-btn color="success" @click="downloadParsedBOM" variant="outlined">
          Download parsed BOM
        </v-btn>
      </div>
    </v-card>
  </v-container>
</template>

<script lang="ts" setup>
import { ref } from 'vue'

const bomFile = ref<File | null>(null)
const context = ref('')
const quantity = ref<number | null>(null)

const loading = ref(false)
const readonly = ref(false)
const pollInterval = ref<number | null>(null)
const pollError = ref<string | null>(null)
const ready = ref(false)

const resetForm = () => {
  bomFile.value = null
  context.value = ''
  quantity.value = null
}

const pollForReady = async () => {
  pollInterval.value = window.setInterval(async () => {
    try {
      const response = await fetch('/api/poll/')
      if (!response.ok) {
        throw new Error('Polling failed')
      }
      const data = await response.json()
      if (data.ready) {
        ready.value = true
        clearInterval(pollInterval.value!)
        pollInterval.value = null
        loading.value = false
        readonly.value = false
      }
    } catch (error) {
      pollError.value = 'Error polling: ' + (error as Error).message
      clearInterval(pollInterval.value!)
      pollInterval.value = null
      loading.value = false
      readonly.value = false
    }
  }, 1000)
}

const onSubmit = async () => {
  if (!bomFile.value || !context.value || !quantity.value) {
    alert('Please fill out all fields and upload a file.')
    return
  }
  loading.value = true
  readonly.value = true
  pollError.value = null
  ready.value = false
  const formData = new FormData()
  formData.append('file', bomFile.value)
  formData.append('context', context.value)
  formData.append('quantity', String(quantity.value))

  try {
    const response = await fetch('/api/upload-csv/', {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) {
      throw new Error('Failed to submit BOM')
    }
    // Start polling
    pollForReady()
  } catch (error) {
    alert('Error submitting BOM: ' + (error as Error).message)
    loading.value = false
    readonly.value = false
  }
}

const downloadParsedBOM = () => {
  window.location.href = '/api/parse/'
}
</script>
