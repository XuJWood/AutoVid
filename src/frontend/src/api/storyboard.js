import api from './index'

export const storyboardApi = {
  // Get all storyboards for a project
  getByProject(projectId) {
    return api.get(`/storyboard/project/${projectId}`)
  },

  // Generate storyboards from script content
  generate(projectId) {
    return api.post(`/storyboard/project/${projectId}/generate`)
  },

  // Generate image for a specific storyboard
  generateImage(storyboardId) {
    return api.post(`/storyboard/${storyboardId}/generate-image`)
  },

  // Generate video for a specific storyboard
  generateVideo(storyboardId) {
    return api.post(`/storyboard/${storyboardId}/generate-video`)
  },

  // Delete a storyboard
  delete(storyboardId) {
    return api.delete(`/storyboard/${storyboardId}`)
  }
}
