import api from './index'

export const modelConfigApi = {
  getAll() {
    return api.get('/model-config')
  },

  get(id) {
    return api.get(`/model-config/${id}`)
  },

  create(data) {
    return api.post('/model-config', data)
  },

  update(id, data) {
    return api.put(`/model-config/${id}`, data)
  },

  delete(id) {
    return api.delete(`/model-config/${id}`)
  },

  test(data) {
    return api.post('/model-config/test', data)
  },

  testConfig(id) {
    return api.post(`/model-config/${id}/test`)
  }
}
