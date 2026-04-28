import api from './index'

export const modelConfigApi = {
  getAll() {
    return api.get('/model-config')
  },

  get(id) {
    return api.get(`/model-config/${id}`)
  },

  getByName(name) {
    return api.get(`/model-config/by-name/${name}`)
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
  },

  async updateOrCreate(data) {
    try {
      const response = await this.getByName(data.name)
      if (response.data && response.data.id) {
        return this.update(response.data.id, data)
      }
    } catch (error) {
      // 如果找不到，创建新的
    }
    return this.create(data)
  }
}
