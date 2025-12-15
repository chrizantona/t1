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
    vacancy_id?: string
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

  // Generate next task with metadata and opening question
  generateNextTaskWithMeta: async (interviewId: number) => {
    const response = await api.post(`/api/interview/${interviewId}/next-task/with-meta`)
    return response.data
  },

  // Get chat messages for a specific task (including opening question)
  getTaskChatMessages: async (interviewId: number, taskId: number) => {
    const response = await api.get(`/api/interview/${interviewId}/tasks/${taskId}/chat-messages`)
    return response.data
  },

  // Get solution follow-up question after task completion
  getSolutionFollowup: async (taskId: number) => {
    const response = await api.post(`/api/interview/tasks/${taskId}/solution-followup`)
    return response.data
  },

  // Get existing solution follow-up for a task
  getExistingFollowup: async (taskId: number) => {
    const response = await api.get(`/api/interview/tasks/${taskId}/solution-followup`)
    return response.data
  },

  // Submit answer to solution follow-up question
  submitFollowupAnswer: async (followupId: number, answerText: string) => {
    const response = await api.post(`/api/interview/solution-followup/${followupId}/answer`, null, {
      params: { answer_text: answerText }
    })
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

  // Create vacancy
  createVacancy: async (data: {
    title: string
    description?: string
    company?: string
    direction: string
    grade_required: string
    skills?: any[]
  }) => {
    const response = await api.post('/api/vacancy/', data)
    return response.data
  },

  // Update vacancy
  updateVacancy: async (vacancyId: string, data: any) => {
    const response = await api.put(`/api/vacancy/${vacancyId}`, data)
    return response.data
  },

  // Delete vacancy
  deleteVacancy: async (vacancyId: string) => {
    const response = await api.delete(`/api/vacancy/${vacancyId}`)
    return response.data
  },
}

// Question Block API (Part 2)
export const questionBlockAPI = {
  // Start question block
  startBlock: async (interviewId: number, questionCount: number = 20) => {
    const response = await api.post('/api/question-block/start', {
      interview_id: interviewId,
      question_count: questionCount
    })
    return response.data
  },

  // Get current question
  getCurrentQuestion: async (blockId: number) => {
    const response = await api.get(`/api/question-block/${blockId}/current`)
    return response.data
  },

  // Submit answer
  submitAnswer: async (answerId: number, candidateAnswer: string) => {
    const response = await api.post('/api/question-block/answer', {
      answer_id: answerId,
      candidate_answer: candidateAnswer
    })
    return response.data
  },

  // Skip question
  skipQuestion: async (answerId: number) => {
    const response = await api.post('/api/question-block/skip', {
      answer_id: answerId
    })
    return response.data
  },

  // Retry question (score halved each retry)
  retryQuestion: async (answerId: number) => {
    const response = await api.post('/api/question-block/retry', {
      answer_id: answerId
    })
    return response.data
  },

  // Get block status
  getBlockStatus: async (blockId: number) => {
    const response = await api.get(`/api/question-block/${blockId}/status`)
    return response.data
  },

  // Get block by interview
  getBlockByInterview: async (interviewId: number) => {
    const response = await api.get(`/api/question-block/interview/${interviewId}/block`)
    return response.data
  },

  // Get detailed statistics
  getStatistics: async (interviewId: number) => {
    const response = await api.get(`/api/question-block/interview/${interviewId}/statistics`)
    return response.data
  },
}

// Auth API
export const authAPI = {
  // Register new user
  register: async (data: {
    email: string
    password: string
    full_name?: string
    role: 'candidate' | 'admin'
  }) => {
    const response = await api.post('/api/auth/register', data)
    return response.data
  },

  // Login
  login: async (email: string, password: string) => {
    const response = await api.post('/api/auth/login', { email, password })
    return response.data
  },

  // Get current user
  getMe: async () => {
    const response = await api.get('/api/auth/me')
    return response.data
  },

  // Demo login as candidate
  demoCandidate: async () => {
    const response = await api.post('/api/auth/demo/candidate')
    return response.data
  },

  // Demo login as admin
  demoAdmin: async () => {
    const response = await api.post('/api/auth/demo/admin')
    return response.data
  },
}

// Anti-Cheat API
export const antiCheatAPI = {
  // Submit anti-cheat events
  submitEvents: async (data: {
    interviewId: number
    events: Array<{
      type: 'keydown' | 'paste' | 'copy' | 'cut' | 'focus' | 'blur' | 'visibility_change' | 'devtools'
      taskId: string
      timestamp: number
      meta?: Record<string, any>
    }>
  }) => {
    const response = await api.post('/api/anti_cheat/events', data)
    return response.data
  },

  // Get trust score
  getTrustScore: async (interviewId: number) => {
    const response = await api.get(`/api/anti_cheat/${interviewId}/trust-score`)
    return response.data
  },
}

// Voice API
export const voiceAPI = {
  // Transcribe audio to text
  transcribe: async (audioBlob: Blob): Promise<{ success: boolean; text: string; message: string }> => {
    const formData = new FormData()
    formData.append('file', audioBlob, 'audio.webm')
    
    const response = await api.post('/api/voice/transcribe', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 60 second timeout for transcription
    })
    return response.data
  },
}

// Set auth token for all requests
export const setAuthToken = (token: string | null) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    localStorage.setItem('vibecode_token', token)
  } else {
    delete api.defaults.headers.common['Authorization']
    localStorage.removeItem('vibecode_token')
  }
}

// Load token from localStorage on init
const savedToken = localStorage.getItem('vibecode_token')
if (savedToken) {
  api.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`
}

export default api

