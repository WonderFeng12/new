import api from './index'

export function listUsers() { return api.get('/users') }
