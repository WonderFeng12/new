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
export function getSheetLogs(id) { return api.get(`/process-sheets/${id}/logs`) }
export function generateConfirmLink(id) { return api.post(`/process-sheets/${id}/generate-confirm-link`) }
export function internalConfirmSheet(id) { return api.post(`/process-sheets/${id}/internal-confirm`) }
export function reopenSheetEdit(id) { return api.post(`/process-sheets/${id}/reopen-edit`) }
export function setConfirmRequirements(id, data) { return api.put(`/process-sheets/${id}/confirm-requirements`, data) }
export function setConfirmUsers(id, user_ids) { return api.put(`/process-sheets/${id}/confirm-users`, user_ids) }
export function forceConfirmSheet(id) { return api.post(`/process-sheets/${id}/force-confirm`) }
export function cancelSheetItem(sheetId, itemId, data) { return api.post(`/process-sheets/${sheetId}/items/${itemId}/cancel`, data) }
export function restoreSheetItem(sheetId, itemId) { return api.post(`/process-sheets/${sheetId}/items/${itemId}/restore`) }
