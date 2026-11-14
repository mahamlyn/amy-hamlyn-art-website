const { test, expect } = require('@playwright/test');

test('contact page exposes labeled enquiry fields and email contact', async ({ page }) => {
  await page.goto('/contact/');

  await expect(page.getByLabel('Name')).toBeVisible();
  await expect(page.getByLabel('Email')).toBeVisible();
  await expect(page.getByLabel('Project type')).toBeVisible();
  await expect(page.getByLabel('Enquiry')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Amy Hamlyn' })).toHaveAttribute(
    'href',
    'mailto:ahamlyn@adam.com.au',
  );
  await expect(page.getByRole('button', { name: 'Send enquiry' })).toBeVisible();
});

test('home page has no horizontal overflow on a mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');

  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(hasHorizontalOverflow).toBe(false);
});