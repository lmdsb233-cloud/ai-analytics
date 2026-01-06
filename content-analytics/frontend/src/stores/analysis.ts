import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Analysis, AnalysisResult, AIOutput, Post } from '@/types'
import * as analysisApi from '@/api/analyses'

export const useAnalysisStore = defineStore('analysis', () => {
  const analyses = ref<Analysis[]>([])
  const currentAnalysis = ref<Analysis | null>(null)
  const results = ref<AnalysisResult[]>([])
  const currentPost = ref<Post | null>(null)
  const currentAIOutput = ref<AIOutput | null>(null)
  const loading = ref(false)

  async function fetchAnalyses(datasetId?: string, page = 1, pageSize = 20) {
    loading.value = true
    try {
      const res = await analysisApi.getAnalyses(datasetId, page, pageSize)
      analyses.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchAnalysis(id: string) {
    const res = await analysisApi.getAnalysis(id)
    const data = res.data
    currentAnalysis.value = data
    // 更新列表中的对应项
    const idx = analyses.value.findIndex(a => a.id === data.id)
    if (idx !== -1) {
      analyses.value[idx] = data
    }
    return data
  }

  async function createAnalysis(datasetId: string, name?: string, config?: any) {
    const res = await analysisApi.createAnalysis({ dataset_id: datasetId, name, config })
    return res.data
  }

  async function fetchResults(analysisId: string, performance?: string, page = 1, pageSize = 50) {
    loading.value = true
    try {
      const res = await analysisApi.getAnalysisResults(analysisId, performance, page, pageSize)
      results.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function triggerAI(analysisId: string) {
    await analysisApi.triggerAIAnalysis(analysisId)
  }

  async function stopAnalysis(analysisId: string) {
    await analysisApi.stopAnalysis(analysisId)
  }

  async function deleteAnalysis(analysisId: string) {
    await analysisApi.deleteAnalysis(analysisId)
  }

  async function fetchPost(postId: string) {
    const res = await analysisApi.getPost(postId)
    currentPost.value = res.data
    return res.data
  }

  async function fetchAIOutput(postId: string, analysisId: string) {
    try {
      const res = await analysisApi.getPostAIOutput(postId, analysisId)
      currentAIOutput.value = res.data
      return res.data
    } catch {
      currentAIOutput.value = null
      return null
    }
  }

  return {
    analyses,
    currentAnalysis,
    results,
    currentPost,
    currentAIOutput,
    loading,
    fetchAnalyses,
    fetchAnalysis,
    createAnalysis,
    fetchResults,
    triggerAI,
    stopAnalysis,
    deleteAnalysis,
    fetchPost,
    fetchAIOutput
  }
})
