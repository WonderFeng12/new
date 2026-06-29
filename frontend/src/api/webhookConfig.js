import api from './index'

export function listWebhooks() { return api.get('/webhook-configs') }
export function createWebhook(data) { return api.post('/webhook-configs', data) }
export function updateWebhook(id, data) { return api.put(`/webhook-configs/${id}`, data) }
export function deleteWebhook(id) { return api.delete(`/webhook-configs/${id}`) }
