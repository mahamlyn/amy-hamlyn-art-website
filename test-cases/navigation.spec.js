const { test, expect } = require('@playwright/test');

test('home page presents the artist portfolio', async ({ page }) => {
  await page.goto('/');

  await expect(page).toHaveTitle('Amy Hamlyn Art');
  await expect(page.getByRole('main')).toBeVisible();
  await expect(
    page.getByRole('heading', {
      level: 1,
      name: 'Thoughtful, expressive artwork with a rich sense of place.',
    }),
  ).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Artist statement' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Selected work' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Upcoming events' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Latest notes' })).toBeVisible();
  await expect(page.locator('link[href^="https://fonts.googleapis.com/css2?"]')).toHaveCount(1);
});

const pages = [
  { name: 'About', path: '/about/', heading: 'Amy Hamlyn' },
  { name: 'Gallery', path: '/gallery/', heading: 'Selected artworks' },
  { name: 'Exhibitions', path: '/exhibitions/', heading: 'Upcoming and recent events' },
  { name: 'Blog', path: '/blog/', heading: 'Studio notes and updates' },
  { name: 'Contact', path: '/contact/', heading: 'Commission an artwork' },
];

for (const sitePage of pages) {
  test(`main navigation opens ${sitePage.name}`, async ({ page }) => {
    await page.goto('/');
    const navigation = page.getByRole('navigation', { name: 'Main navigation' });
    const expectedUrl = new URL(sitePage.path, page.url()).toString();

    await navigation.getByRole('link', { name: sitePage.name, exact: true }).click();

    await expect(page).toHaveURL(expectedUrl);
    await expect(
      page.getByRole('heading', { level: 1, name: sitePage.heading, exact: true }),
    ).toBeVisible();
  });
}

test('shared footer uses the contact email on every page', async ({ page }) => {
  const paths = ['/', ...pages.map((sitePage) => sitePage.path), '/blog/art-by-amy-blog-52/'];

  for (const path of paths) {
    await page.goto(path);
    const footer = page.getByRole('contentinfo');

    await expect(footer.getByRole('link', { name: 'ahamlyn@adam.com.au', exact: true }))
      .toHaveAttribute('href', 'mailto:ahamlyn@adam.com.au');
    await expect(footer).not.toContainText('hello@amyhamlynart.com');
  }
});