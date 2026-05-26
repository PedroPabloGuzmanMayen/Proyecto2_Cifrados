//Aqui se va a utilizar para llamar a las funciones fetch para conecta a la API 

const BASE = 'http://localhost:8000'

const headers = (token) => ({
  'Content-Type': 'application/json',
  ...(token ? { Authorization: `Bearer ${token}` } : {}),
})

const handle = async (res) => {
  const data = await res.json()
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`)
  return data
}

export const api = {
  // Auth
  registro: (body) =>
    fetch(`${BASE}/registro`, { method: 'POST', headers: headers(), body: JSON.stringify(body) }).then(handle),

  login: (body) =>
    fetch(`${BASE}/login`, { method: 'POST', headers: headers(), body: JSON.stringify(body) }).then(handle),

  loginMFA: (body) =>
    fetch(`${BASE}/auth/mfa/login`, { method: 'POST', headers: headers(), body: JSON.stringify(body) }).then(handle),

  enableMFA: (token) =>
    fetch(`${BASE}/auth/mfa/enable`, { method: 'POST', headers: headers(token) }).then(handle),

  verifyMFA: (user_id, totp_code) =>
    fetch(`${BASE}/auth/mfa/verify?user_id=${user_id}&totp_code=${totp_code}`, { method: 'POST', headers: headers() }).then(handle),

  // Users
  getUserKey: (userId) =>
    fetch(`${BASE}/users/${userId}/key`, { headers: headers() }).then(handle),

  // Messages
  getMessages: (userId) =>
    fetch(`${BASE}/messages/${userId}`, { headers: headers() }).then(handle),

  sendMessage: (body) =>
    fetch(`${BASE}/individual_message/`, { method: 'POST', headers: headers(), body: JSON.stringify(body) }).then(handle),

  decryptMessage: (userId, msgId, password) =>
    fetch(`${BASE}/messages/${userId}/decrypt/${msgId}`, {
      method: 'POST', headers: headers(), body: JSON.stringify({ password }),
    }).then(handle),

  verifySignature: (msgId, password) =>
    fetch(`${BASE}/messages/${msgId}/verify`, {
      method: 'POST', headers: headers(), body: JSON.stringify({ password }),
    }).then(handle),

  // Group messages
  sendGroupMessage: (body) =>
    fetch(`${BASE}/group_message`, { method: 'POST', headers: headers(), body: JSON.stringify(body) }).then(handle),

  // Groups
  createGroup: (body) =>
    fetch(`${BASE}/groups`, { method: 'POST', headers: headers(), body: JSON.stringify(body) }).then(handle),

  addMember: (groupId, userId) =>
    fetch(`${BASE}/groups/${groupId}/members`, {
      method: 'POST', headers: headers(), body: JSON.stringify({ user_id: userId }),
    }).then(handle),

  // Blockchain
  verifyBlockchain: () =>
    fetch(`${BASE}/blockchain/verify`, { headers: headers() }).then(handle),
}