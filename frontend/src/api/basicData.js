import api from './index'

export function listBasicData(category) {
  return api.get(`/basic-data/${category}`)
}

export function createBasicData(category, data) {
  return api.post(`/basic-data/${category}`, data)
}

export function updateBasicData(category, id, data) {
  return api.put(`/basic-data/${category}/${id}`, data)
}

export function deleteBasicData(category, id) {
  return api.delete(`/basic-data/${category}/${id}`)
}

export function getColorMapping() {
  return api.get('/basic-data/mapping/color')
}
