import api from './index'

export const videosApi = {
  getAll(projectId = null, status = null) {
    const params = {}
    if (projectId) params.project_id = projectId
    if (status) params.status = status
    return api.get('/videos', { params })
  },

  get(id) {
    return api.get(`/videos/${id}`)
  },

  generate(data) {
    return api.post('/videos/generate', data)
  },

  regenerate(id) {
    return api.post(`/videos/${id}/regenerate`)
  },

  delete(id) {
    return api.delete(`/videos/${id}`)
  },

  getStatus(id) {
    return api.get(`/videos/${id}/status`)
  }
}
