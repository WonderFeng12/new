import { defineStore } from 'pinia'
import { getMyPermissions } from '../api/permissions'

export const usePermissionStore = defineStore('permission', {
  state: () => ({
    permissions: [],
    definitions: [],
    loaded: false,
  }),
  getters: {
    hasPermission: (state) => {
      return (perm) => state.permissions.includes(perm)
    },
  },
  actions: {
    async fetchMyPermissions() {
      const res = await getMyPermissions()
      this.permissions = res.data
      this.loaded = true
    },
    setDefinitions(defs) {
      this.definitions = defs
    },
    reset() {
      this.permissions = []
      this.definitions = []
      this.loaded = false
    },
  },
})
