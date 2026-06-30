import api from './index'

export function getPermissionDefinitions() { return api.get('/permissions/definitions') }
export function getAllPermissions() { return api.get('/permissions') }
export function updatePermissions(data) { return api.put('/permissions', data) }
export function getMyPermissions() { return api.get('/permissions/my') }
