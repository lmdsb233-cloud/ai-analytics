import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Dataset } from '@/types'
import * as datasetApi from '@/api/datasets'

export const useDatasetStore = defineStore('dataset', () => {
  const datasets = ref<Dataset[]>([])
  const total = ref(0)
  const loading = ref(false)
  const currentDataset = ref<Dataset | null>(null)

  async function fetchDatasets(page = 1, pageSize = 20) {
    loading.value = true
    try {
      const res = await datasetApi.getDatasets(page, pageSize)
      datasets.value = res.data.items
      total.value = res.data.total
    } finally {
      loading.value = false
    }
  }

  async function fetchDataset(id: string) {
    const res = await datasetApi.getDataset(id)
    currentDataset.value = res.data
    return res.data
  }

  async function uploadDataset(name: string, file: File) {
    const formData = new FormData()
    formData.append('name', name)
    formData.append('file', file)
    const res = await datasetApi.uploadDataset(formData)
    return res.data
  }

  async function deleteDataset(id: string) {
    await datasetApi.deleteDataset(id)
    datasets.value = datasets.value.filter(d => d.id !== id)
    total.value--
  }

  return {
    datasets,
    total,
    loading,
    currentDataset,
    fetchDatasets,
    fetchDataset,
    uploadDataset,
    deleteDataset
  }
})
