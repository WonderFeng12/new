import api from './index'

export function listUsers() { return api.get('/users') }
export function createUser(data) { return api.post('/users', data) }
export function updateUser(id, data) { return api.put(`/users/${id}`, data) }
export function resetPassword(id, data) { return api.put(`/users/${id}/reset-password`, data) }
export function deleteUser(id) { return api.delete(`/users/${id}`) }
