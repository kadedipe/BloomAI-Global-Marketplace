import {expect, test} from '@playwright/test';

test('public marketplace, API link and five-result AI Lab work', async ({page}) => {
  await page.goto('/');
  await expect(page.getByRole('heading', {name: /Explore the marketplace/i})).toBeVisible();
  await expect(page.getByRole('link', {name: 'API'})).toHaveAttribute('href', /\/docs$/);
  const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=', 'base64');
  await page.locator('#ai input[type=file]').setInputFiles({name: 'flower.png', mimeType: 'image/png', buffer: png});
  await page.getByRole('button', {name: /Identify flower/i}).click();
  await expect(page.locator('.prediction')).toHaveCount(5, {timeout: 30_000});
});

test('vendor session persists and owned product can be created and deleted', async ({page}) => {
  test.skip(!process.env.E2E_VENDOR_EMAIL || !process.env.E2E_VENDOR_PASSWORD, 'Staging vendor credentials are required');
  await page.goto('/');
  await page.getByRole('button', {name: 'Sign in'}).click();
  await page.getByRole('textbox', {name: 'Email address'}).fill(process.env.E2E_VENDOR_EMAIL);
  await page.getByLabel('Password').fill(process.env.E2E_VENDOR_PASSWORD);
  await page.getByRole('button', {name: 'Sign in', exact: true}).last().click();
  await expect(page.locator('.user-chip')).toBeVisible();
  await page.reload();
  await expect(page.locator('.user-chip')).toBeVisible();
  const productName = `E2E Test Flower ${Date.now()}`;
  await page.getByLabel('Product name').fill(productName);
  await page.getByLabel('Price').locator('input').fill('1000');
  await page.getByLabel('Description').fill('Automated staging smoke test; safe to delete.');
  await page.getByRole('button', {name: /Publish product/i}).click();
  const card = page.locator('article').filter({hasText: productName});
  await expect(card).toBeVisible();
  page.once('dialog', dialog => dialog.accept());
  await card.getByRole('button', {name: 'Delete'}).click();
  await expect(card).toHaveCount(0);
  await page.getByRole('button', {name: 'Logout'}).click();
  await expect(page.getByRole('button', {name: 'Sign in'})).toBeVisible();
});
