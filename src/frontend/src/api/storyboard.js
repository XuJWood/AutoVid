import api from './index'

export const storyboardApi = {
  // Get all episodes for a project (includes segments)
  getByProject(projectId) {
    return api.get(`/storyboard/project/${projectId}`)
  },

  // Generate episodes from script content (creates episodes + segments)
  generate(projectId) {
    return api.post(`/storyboard/project/${projectId}/generate`)
  },

  // Generate cover image for an episode
  generateImage(storyboardId) {
    return api.post(`/storyboard/${storyboardId}/generate-image`)
  },

  // [DEPRECATED] Generate video for an episode — redirects to segment generation if segments exist
  generateVideo(storyboardId, { audio_url, duration, resolution } = {}) {
    return api.post(`/storyboard/${storyboardId}/generate-video`, { audio_url, duration, resolution })
  },

  // [DEPRECATED] Generate audio — no longer needed with Seedance (video+audio)
  generateAudio(storyboardId, dialogue, voice) {
    return api.post(`/storyboard/${storyboardId}/generate-audio`, { dialogue, voice })
  },

  // Generate video for a single segment (Seedance or other model)
  generateSegmentVideo(segmentId, { provider, api_key, model, duration, ratio, resolution } = {}) {
    return api.post(`/storyboard/segment/${segmentId}/generate-video`, { provider, api_key, model, duration, ratio, resolution })
  },

  // Generate all segment videos for an episode
  generateAllSegments(storyboardId, { provider, api_key, model, duration, ratio, resolution } = {}) {
    return api.post(`/storyboard/${storyboardId}/generate-all-segments`, { provider, api_key, model, duration, ratio, resolution })
  },

  // Delete a segment
  deleteSegment(segmentId) {
    return api.delete(`/storyboard/segment/${segmentId}`)
  },

  // Delete an episode (and all its segments)
  delete(storyboardId) {
    return api.delete(`/storyboard/${storyboardId}`)
  }
}
