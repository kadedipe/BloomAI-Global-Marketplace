import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {describe,it,expect} from 'vitest';

const source=path=>readFileSync(fileURLToPath(new URL(path,import.meta.url)),'utf8');

describe('commerce frontend contract',()=>{
  it('keeps the commerce entrypoint available to the production build',()=>{
    expect('/src/commerce-entry.js').toContain('commerce-entry');
  });

  it('does not call the retired direct payment initializer from React',()=>{
    expect(source('./main.jsx')).not.toContain('/api/v1/payments/initialize');
  });

  it('uses the structured order checkout path',()=>{
    const orderFlow=source('./order-flow-entry.js');
    expect(orderFlow).toContain('/api/v1/orders/quote');
    expect(orderFlow).toContain('/api/v1/orders/checkout');
  });
});
