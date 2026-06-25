import api from './index'

export function uploadImages(files) {
  const formData = new FormData()
  files.forEach(f => formData.append('files', f))
  return api.post('/upload/images', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
