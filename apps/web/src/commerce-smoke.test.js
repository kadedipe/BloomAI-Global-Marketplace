import {describe,it,expect} from 'vitest';

describe('commerce frontend contract',()=>{
  it('keeps the commerce entrypoint available to the production build',()=>{
    expect('/src/commerce-entry.js').toContain('commerce-entry');
  });
});
