import api from './index'

export const promptTemplateApi = {
  getAll(type = null) {
    const params = type ? { type } : {}
    return api.get('/prompt-templates', { params })
  },

  get(id) {
    return api.get(`/prompt-templates/${id}`)
  },

  create(data) {
    return api.post('/prompt-templates', data)
  },

  update(id, data) {
    return api.put(`/prompt-templates/${id}`, data)
  },

  delete(id) {
    return api.delete(`/prompt-templates/${id}`)
  },

  render(templateId, variables) {
    return api.post('/prompt-templates/render', { template_id: templateId, variables })
  },

  initDefaults() {
    return api.post('/prompt-templates/init-defaults')
  }
}
