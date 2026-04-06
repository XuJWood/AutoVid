import api from './index'

export const charactersApi = {
  getAll(projectId = null, style = null) {
    const params = {}
    if (projectId) params.project_id = projectId
    if (style) params.style = style
    return api.get('/characters', { params })
  },

  get(id) {
    return api.get(`/characters/${id}`)
  },

  create(data) {
    return api.post('/characters', data)
  },

  update(id, data) {
    return api.put(`/characters/${id}`, data)
  },

  delete(id) {
    return api.delete(`/characters/${id}`)
  },

  generateImage(characterId, data) {
    return api.post(`/characters/${characterId}/generate-image`, data)
  },

  selectImage(characterId, imageUrl) {
    return api.post(`/characters/${characterId}/select-image`, null, {
      params: { image_url: imageUrl }
    })
  },

  uploadImage(characterId, file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/characters/${characterId}/upload-image`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}
