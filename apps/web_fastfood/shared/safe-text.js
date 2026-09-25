/* Text and JavaScript-string encoders for dashboard template interpolation. */
window.escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c =>
  ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
window.escapeJSAttribute = value => String(value ?? '').replace(/[\\'"<>&\r\n\u2028\u2029]/g,
  c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));
