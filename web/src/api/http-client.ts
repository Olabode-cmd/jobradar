import { GodspeedClient } from '@thraggs/godspeed';

// allowPrivateNetworks: godspeed's SSRF guard rejects loopback hosts, and this
// dashboard only ever talks to the localhost API through the same origin.
export const http = new GodspeedClient({
  baseURL: '/api',
  timeout: 8000,
  retries: 1,
  allowPrivateNetworks: true,
});
