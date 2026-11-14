const { test, expect } = require('@playwright/test');

test('gallery shows artwork with descriptive, loaded images', async ({ page }) => {
  await page.goto('/gallery/');

  const artworks = page.locator('article.art-card');
  await expect(artworks).toHaveCount(3);
  for (const title of ['Forest Alive', 'Sun Setting', 'Structural']) {
    await expect(page.getByRole('heading', { name: title, exact: true })).toBeVisible();
  }

  for (const image of await page.locator('article.art-card img').all()) {
    await image.scrollIntoViewIfNeeded();
    await expect(image).toHaveAttribute('alt', /.+/);
    await expect.poll(() => image.evaluate((element) => element.naturalWidth > 0)).toBe(true);
  }
});

test('exhibitions list their dates, titles, and venues', async ({ page }) => {
  await page.goto('/exhibitions/');

  const events = page.locator('article.timeline-item');
  await expect(events).toHaveCount(2);
  await expect(page.getByRole('heading', { name: 'Autumn Open Studio' })).toBeVisible();
  await expect(page.getByText('The Old Mill Studio, Bristol')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Winter Showcase' })).toBeVisible();
});

test('a blog summary opens its full post', async ({ page }) => {
  await page.goto('/blog/');

  const firstPost = page.locator('article.post-summary').first();
  await expect(firstPost).toBeVisible();
  const title = await firstPost.getByRole('heading').innerText();
  await firstPost.getByRole('link').click();

  await expect(page.getByRole('heading', { level: 1, name: title, exact: true })).toBeVisible();
  await expect(page.locator('main article')).toBeVisible();
});

test('about portrait placeholder uses native figure semantics', async ({ page }) => {
  await page.goto('/about/');

  const portrait = page.locator('figure.about-portrait');
  await expect(portrait).toBeVisible();
  await expect(portrait.locator('figcaption')).toHaveText('Portrait to be added');
  await expect(portrait).not.toHaveAttribute('role', 'img');
});