#!/usr/bin/env node
/** Node CLI — calls POST /convert on local FastAPI service. */

const http = require('http');

const [,, amount, from, to] = process.argv;
const base = process.env.CONVERT_URL || 'http://127.0.0.1:8000';

if (!amount || !from || !to) {
  console.error('Usage: node index.js <amount> <from> <to>');
  process.exit(1);
}

const body = JSON.stringify({ amount: parseFloat(amount), from, to });
const url = new URL('/convert', base);

const req = http.request(
  {
    hostname: url.hostname,
    port: url.port || 80,
    path: url.pathname,
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
  },
  (res) => {
    let data = '';
    res.on('data', (c) => { data += c; });
    res.on('end', () => {
      if (res.statusCode >= 400) {
        console.error('Error:', res.statusCode, data);
        process.exit(1);
      }
      const j = JSON.parse(data);
      console.log('┌─────────┬──────────┐');
      console.log(`│ Amount  │ ${j.amount}`);
      console.log(`│ From    │ ${j.from}`);
      console.log(`│ To      │ ${j.to}`);
      console.log(`│ Result  │ ${j.converted}`);
      console.log(`│ Rate    │ ${j.rate}`);
      console.log('└─────────┴──────────┘');
    });
  },
);
req.on('error', (e) => { console.error(e.message); process.exit(1); });
req.write(body);
req.end();
