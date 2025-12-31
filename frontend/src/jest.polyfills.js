// Jest polyfills - loaded before tests via setupFiles
// Required for MSW v2 which uses TextEncoder/TextDecoder

const { TextEncoder, TextDecoder } = require('util');

global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;

// BroadcastChannel polyfill for MSW
class BroadcastChannelPolyfill {
  constructor(name) { this.name = name; }
  postMessage() {}
  close() {}
  addEventListener() {}
  removeEventListener() {}
  dispatchEvent() { return true; }
}
global.BroadcastChannel = BroadcastChannelPolyfill;

// Request/Response polyfills using whatwg-fetch
require('whatwg-fetch');
