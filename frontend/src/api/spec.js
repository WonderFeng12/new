import api from './index'

export function listSpecs(params) { return api.get('/specs', { params }) }
export function getSpec(id) { return api.get(`/specs/${id}`) }
export function createSpec(data) { return api.post('/specs', data) }
export function updateSpec(id, data) { return api.put(`/specs/${id}`, data) }
export function deleteSpec(id) { return api.delete(`/specs/${id}`) }
