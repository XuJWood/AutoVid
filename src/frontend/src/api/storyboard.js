import api from './index'

export const storyboardApi = {
  // Get all episodes for a project
  getByProject(projectId) {
    return api.get(`/storyboard/project/${projectId}`)
  },

  // Generate episodes from script content
  generate(projectId) {
    return api.post(`/storyboard/project/${projectId}/generate`)
  },

  // Generate cover image for an episode
  generateImage(storyboardId) {
    return api.post(`/storyboard/${storyboardId}/generate-image`)
  },

  // Generate anime video for an episode (~20s)
  generateVideo(storyboardId) {
    return api.post(`/storyboard/${storyboardId}/generate-video`)
  },

  // Generate audio dubbing for an episode (TTS + FFmpeg merge)
  generateAudio(storyboardId, dialogue, voice) {
    return api.post(`/storyboard/${storyboardId}/generate-audio`, { dialogue, voice })
  },

  // Delete an episode
  delete(storyboardId) {
    return api.delete(`/storyboard/${storyboardId}`)
  }
}
