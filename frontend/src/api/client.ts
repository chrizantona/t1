import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interview API
export const interviewAPI = {
  // Start new interview
  startInterview: async (data: {
    candidate_name?: string
    candidate_email?: string
    selected_level: string
    direction: string
    cv_text?: string
  }) => {
    const response = await api.post('/api/interview/start', data)
    return response.data
  },

  // Get interview details
  getInterview: async (interviewId: number) => {
    const response = await api.get(`/api/interview/${interviewId}`)
    return response.data
  },

  // Get tasks for interview
  getTasks: async (interviewId: number) => {
    const response = await api.get(`/api/interview/${interviewId}/tasks`)
    return response.data
  },

  // Submit code
  submitCode: async (data: {
    task_id: number
    code: string
    language: string
  }) => {
    const response = await api.post('/api/interview/submit', data)
    return response.data
  },

  // Send chat message
  sendMessage: async (data: {
    interview_id: number
    content: string
    task_id?: number
  }) => {
    const response = await api.post('/api/interview/chat', data)
    return response.data
  },

  // Request hint
  requestHint: async (data: {
    task_id: number
    hint_level: string
    current_code?: string
  }) => {
    const response = await api.post('/api/interview/hint', data)
    return response.data
  },

  // Get final report
  getFinalReport: async (interviewId: number) => {
    const response = await api.get(`/api/interview/${interviewId}/report`)
    return response.data
  },

  // Complete interview
  completeInterview: async (interviewId: number) => {
    const response = await api.post(`/api/interview/${interviewId}/complete`)
    return response.data
  },
}

// Resume API
export const resumeAPI = {
  // Analyze CV
  analyzeCV: async (cvText: string) => {
    const response = await api.post('/api/resume/analyze', { cv_text: cvText })
    return response.data
  },
}

// Admin API
export const adminAPI = {
  // List all interviews
  listInterviews: async (skip = 0, limit = 100) => {
    const response = await api.get('/api/admin/interviews', {
      params: { skip, limit },
    })
    return response.data
  },

  // Get statistics
  getStatistics: async () => {
    const response = await api.get('/api/admin/statistics')
    return response.data
  },
}

export default api

