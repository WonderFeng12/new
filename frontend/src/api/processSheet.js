import api from './index'

export function listSheets(params) { return api.get('/process-sheets', { params }) }
export function getSheet(id) { return api.get(`/process-sheets/${id}`) }
export function createSheet(data) { return api.post('/process-sheets', data) }
export function confirmSheet(id) { return api.put(`/process-sheets/${id}/confirm`) }
export function dispatchSheet(id) { return api.post(`/process-sheets/${id}/dispatch`) }
export function printSheet(id) { return api.get(`/process-sheets/${id}/print`, { responseType: 'blob' }) }
export function deleteSheet(id) { return api.delete(`/process-sheets/${id}`) }
export function updateSheetDetail(id, data) { return api.put(`/process-sheets/${id}/detail`, data) }
export function markVersion(id, data) { return api.post(`/process-sheets/${id}/mark-version`, data) }
