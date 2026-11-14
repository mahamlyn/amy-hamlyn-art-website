const { test, expect } = require('@playwright/test');

test('contact page exposes labeled enquiry fields and email contact', async ({ page }) => {
  await page.goto('/contact/');

  await expect(page.getByLabel('Name')).toBeVisible();
  await expect(page.getByLabel('Email')).toBeVisible();
  await expect(page.getByLabel('Project type')).toBeVisible();
  await expect(page.getByLabel('Enquiry')).toBeVisible();
  await expect(page.getByRole('link', { name: 'Amy Hamlyn', exact: true })).toHaveAttribute(
    'href',
    'mailto:ahamlyn@adam.com.au',
  );
  await expect(page.getByRole('button', { name: 'Send enquiry' })).toBeVisible();
});

test('contact form is disabled until the enquiry service is configured', async ({ page }) => {
  await page.goto('/contact/');

  await expect(page.getByLabel('Name')).toBeVisible();
  await expect(page.getByLabel('Email')).toBeVisible();
  await expect(page.getByLabel('Project type')).toBeVisible();
  await expect(page.getByLabel('Enquiry')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Send enquiry' })).toBeDisabled();
  await expect(page.locator('#contact-status')).toContainText('temporarily disabled');
  await expect(page.locator('#contact-status').getByRole('link', { name: 'ahamlyn@adam.com.au' }))
    .toHaveAttribute('href', 'mailto:ahamlyn@adam.com.au');
  await expect(page.locator('form')).not.toHaveAttribute('action', /formsubmit\.co/);
});

test('home page has no horizontal overflow on a mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');

  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(hasHorizontalOverflow).toBe(false);
});