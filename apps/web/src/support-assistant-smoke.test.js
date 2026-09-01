import {describe,it,expect} from 'vitest';
import fs from 'node:fs';
import path from 'node:path';

describe('support assistant integration',()=>{
  it('loads the support assistant from the marketplace page',()=>{
    const html=fs.readFileSync(path.resolve('index.html'),'utf8');
    expect(html).toContain('/src/support-assistant-entry.js');
  });

  it('keeps provider credentials out of browser code',()=>{
    const source=fs.readFileSync(path.resolve('src/support-assistant-entry.js'),'utf8');
    expect(source).not.toContain('SUPPORT_AI_API_KEY');
    expect(source).not.toContain('Authorization: Bearer');
    expect(source).toContain('/api/v1/support/assistant');
    expect(source).toContain('/api/v1/support/escalate');
  });
});
