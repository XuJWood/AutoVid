import api from './index'

export const projectsApi = {
  getAll(type = null, status = null) {
    const params = {}
    if (type) params.type = type
    if (status) params.status = status
    return api.get('/projects', { params })
  },

  get(id) {
    return api.get(`/projects/${id}`)
  },

  create(data) {
    return api.post('/projects', data)
  },

  update(id, data) {
    return api.put(`/projects/${id}`, data)
  },

  delete(id) {
    return api.delete(`/projects/${id}`)
  },

  generateScript(projectId, data) {
    return api.post(`/projects/${projectId}/script/generate`, data)
  },

  getCharacters(projectId) {
    return api.get(`/projects/${projectId}/characters`)
  }
}
