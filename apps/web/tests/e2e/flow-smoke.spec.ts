import { test, expect } from '@playwright/test';

test('unauthenticated stage-navigation smoke flow', async ({ page }) => {
  await page.goto('/script');
  await expect(page).toHaveURL(/\/login/);

  await page.goto('/voiceover');
  await expect(page.getByRole('heading', { name: 'Voice Generation' })).toBeVisible();

  await page.goto('/images');
  await expect(page.getByRole('heading', { name: 'Images' })).toBeVisible();
  await expect(page.getByText('No Project Selected')).toBeVisible();

  await page.goto('/video');
  await expect(page.getByRole('heading', { name: 'Video Compilation' })).toBeVisible();
  await expect(page.getByText('No Project Selected')).toBeVisible();
});
