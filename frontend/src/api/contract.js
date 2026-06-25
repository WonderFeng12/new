import api from './index'

export function listContracts(params) { return api.get('/contracts', { params }) }
export function getContract(id) { return api.get(`/contracts/${id}`) }
export function createContract(data) { return api.post('/contracts', data) }
export function updateContract(id, data) { return api.put(`/contracts/${id}`, data) }
export function deleteContract(id) { return api.delete(`/contracts/${id}`) }
export function generateConfirmImage(id) { return api.post(`/contracts/${id}/confirm-image`) }
export function markConfirmed(id) { return api.post(`/contracts/${id}/confirm`) }
export function getVersions(id) { return api.get(`/contracts/${id}/versions`) }
export function getAvailableContracts() { return api.get('/contracts/available') }
