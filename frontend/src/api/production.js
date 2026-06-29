import api from './index'

export function listProcessSteps(params) { return api.get('/process-steps', { params }) }
export function createProcessStep(data) { return api.post('/process-steps', data) }
export function updateProcessStep(id, data) { return api.put(`/process-steps/${id}`, data) }
export function deleteProcessStep(id) { return api.delete(`/process-steps/${id}`) }
export function setStepAssignees(id, data) { return api.put(`/process-steps/${id}/assignees`, data) }

export function advanceItem(id, data) { return api.post(`/contract-items/${id}/advance`, data) }
export function rollbackItem(id, data) { return api.post(`/contract-items/${id}/rollback`, data) }
export function reworkItem(id, data) { return api.post(`/contract-items/${id}/rework`, data) }
export function cancelItem(id, data) { return api.post(`/contract-items/${id}/cancel`, data) }
export function releaseYarnPlan(id, data) { return api.post(`/contract-items/${id}/yarn-plan`, data) }
export function pushDownItem(id, data = {}) { return api.post(`/contract-items/${id}/push-down`, data) }

export function getItemLogs(id) { return api.get(`/contract-items/${id}/logs`) }
export function getContractLogs(id) { return api.get(`/contracts/${id}/production-logs`) }

export function getMyTasks() { return api.get('/my-tasks') }

export function getWecomSettings() { return api.get('/settings/wecom') }
export function updateWecomSettings(data) { return api.put('/settings/wecom', data) }
export function updateMyWecom(data) { return api.put('/users/me/wecom', data) }
