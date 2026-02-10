import { test, expect } from '@playwright/test';

test.describe('public page smoke', () => {
  test('home renders sign-in CTA for anonymous users', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'RealEstate Video Pro' })).toBeVisible();
    await expect(page.getByRole('main').getByRole('link', { name: 'Sign In' })).toBeVisible();
  });

  test('auth pages render core forms', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: 'Sign in to your account' })).toBeVisible();

    await page.goto('/signup');
    await expect(page.getByRole('heading', { name: 'Create your account' })).toBeVisible();

    await page.goto('/forgot');
    await expect(page.getByRole('heading', { name: 'Reset your password' })).toBeVisible();

    await page.goto('/reset-password');
    await expect(page.getByRole('heading', { name: 'Set a new password' })).toBeVisible();
  });
});
