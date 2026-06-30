import { usePermissionStore } from '../store/permissions'

export function usePermission() {
  const store = usePermissionStore()

  function hasPermission(perm) {
    return store.hasPermission(perm)
  }

  return { hasPermission }
}
