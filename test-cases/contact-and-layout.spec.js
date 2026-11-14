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

test('contact form shows loading and success and ignores duplicate submissions', async ({ page }) => {
  let releaseResponse;
  let requestCount = 0;
  const responseGate = new Promise((resolve) => {
    releaseResponse = resolve;
  });

  await page.route('https://formsubmit.co/ajax/amyhamlyn@live.com', async (route) => {
    requestCount += 1;
    expect(route.request().postDataJSON()).toMatchObject({
      name: 'Test Sender',
      email: 'sender@example.com',
      projectType: 'Commission',
      enquiry: 'Testing the contact form.',
      _replyto: 'sender@example.com',
    });
    await responseGate;
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: 'true', message: 'Test enquiry sent.' }),
    });
  });
  await page.goto('/contact/');
  await page.getByLabel('Name').fill('Test Sender');
  await page.getByLabel('Email').fill('sender@example.com');
  await page.getByLabel('Enquiry').fill('Testing the contact form.');

  const form = page.locator('#contact-form');
  const submitButton = page.getByRole('button', { name: 'Send enquiry' });
  await form.evaluate((element) => element.requestSubmit());

  await expect(page.locator('#contact-status')).toHaveText('Sending your enquiry...');
  await expect(submitButton).toBeDisabled();
  await form.evaluate((element) => element.requestSubmit());
  expect(requestCount).toBe(1);

  releaseResponse();
  await expect(page.locator('#contact-status')).toHaveText('Test enquiry sent.');
  await expect(submitButton).toBeEnabled();
});

test('contact form shows an error when the API fails', async ({ page }) => {
  await page.route('https://formsubmit.co/ajax/amyhamlyn@live.com', (route) => route.fulfill({
    status: 502,
    contentType: 'application/json',
    body: JSON.stringify({ success: 'false', message: 'FormSubmit could not accept this enquiry.' }),
  }));
  await page.goto('/contact/');
  await page.getByLabel('Name').fill('Test Sender');
  await page.getByLabel('Email').fill('sender@example.com');
  await page.getByLabel('Enquiry').fill('Testing the error state.');
  await page.locator('#contact-form').evaluate((form) => form.requestSubmit());

  await expect(page.locator('#contact-status')).toHaveText('FormSubmit could not accept this enquiry.');
  await expect(page.getByRole('button', { name: 'Send enquiry' })).toBeEnabled();
});

test('home page has no horizontal overflow on a mobile viewport', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');

  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(hasHorizontalOverflow).toBe(false);
});