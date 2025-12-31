'use server';

import { revalidatePath } from 'next/cache';

export async function revalidateCompetitors() {
  revalidatePath('/competitors');
}

export async function revalidateDashboard() {
  revalidatePath('/');
}

export async function revalidateAlerts() {
  revalidatePath('/alerts');
}

export async function revalidateAll() {
  revalidatePath('/');
  revalidatePath('/competitors');
  revalidatePath('/alerts');
}
