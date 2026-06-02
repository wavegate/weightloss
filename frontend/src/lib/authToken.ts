type TokenGetter = () => Promise<string | null>

let getAuthToken: TokenGetter | null = null

export function setAuthTokenGetter(getter: TokenGetter) {
  getAuthToken = getter
}

export async function getBearerToken(): Promise<string | null> {
  if (!getAuthToken) {
    return null
  }
  return getAuthToken()
}
