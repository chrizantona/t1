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

  // Generate next task
  generateNextTask: async (interviewId: number) => {
    const response = await api.post(`/api/interview/${interviewId}/next-task`)
    return response.data
  },

  // ============ V2 API Methods ============

  // Start new interview with V2 flow (3 tasks at once)
  startInterviewV2: async (data: {
    candidate_name?: string
    candidate_email?: string
    selected_level: string
    direction: string
    cv_text?: string
  }) => {
    const response = await api.post('/api/interview/v2/start', data)
    return response.data
  },

  // Get interview details V2
  getInterviewV2: async (interviewId: number) => {
    const response = await api.get(`/api/interview/v2/${interviewId}`)
    return response.data
  },

  // Get all 3 tasks
  getAllTasks: async (interviewId: number) => {
    const response = await api.get(`/api/interview/v2/${interviewId}/tasks`)
    return response.data
  },

  // Get interview progress
  getProgress: async (interviewId: number) => {
    const response = await api.get(`/api/interview/v2/${interviewId}/progress`)
    return response.data
  },

  // Proceed to theory stage
  proceedToTheory: async (interviewId: number) => {
    const response = await api.post(`/api/interview/v2/${interviewId}/proceed-to-theory`)
    return response.data
  },

  // Get next theory question
  getNextQuestion: async (interviewId: number) => {
    const response = await api.get(`/api/interview/v2/${interviewId}/next-question`)
    return response.data
  },

  // Submit theory answer
  submitTheoryAnswer: async (data: { answer_id: number; answer_text: string }) => {
    const response = await api.post('/api/interview/v2/submit-answer', data)
    return response.data
  },

  // Get all theory answers
  getTheoryAnswers: async (interviewId: number) => {
    const response = await api.get(`/api/interview/v2/${interviewId}/theory-answers`)
    return response.data
  },

  // Complete interview V2 and get final scores
  completeInterviewV2: async (interviewId: number) => {
    const response = await api.post(`/api/interview/v2/${interviewId}/complete`)
    return response.data
  },
}

// Resume API
export const resumeAPI = {
  // Analyze CV from text
  analyzeCV: async (cvText: string) => {
    const response = await api.post('/api/resume/analyze', { cv_text: cvText })
    return response.data
  },

  // Upload and analyze CV file (PDF or TXT)
  uploadCV: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/api/resume/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
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

// Vacancy API
export const vacancyAPI = {
  // List all vacancies
  listVacancies: async (direction?: string, grade?: string) => {
    const params: Record<string, string> = {}
    if (direction) params.direction = direction
    if (grade) params.grade = grade
    const response = await api.get('/api/vacancy/', { params })
    return response.data
  },

  // Get vacancy details
  getVacancy: async (vacancyId: string) => {
    const response = await api.get(`/api/vacancy/${vacancyId}`)
    return response.data
  },

  // Get vacancy skills
  getVacancySkills: async (vacancyId: string) => {
    const response = await api.get(`/api/vacancy/skills/${vacancyId}`)
    return response.data
  },
}

export default api

