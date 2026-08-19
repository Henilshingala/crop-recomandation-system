/**
 * API Service for Government Schemes Recommendation
 */

import { API_BASE_URL } from "./api";

export interface Scheme {
  scheme_name: string;
  description: string;
  short_description: string;
  benefits: string;
  eligibility: string;
  categories: string[];
  states: string[];
  url: string;
}

export interface SchemeOptions {
  states: string[];
  categories: string[];
}

export async function getSchemes(params: Record<string, string>): Promise<Scheme[]> {
  const query = new URLSearchParams(params).toString();
  const response = await fetch(`${API_BASE_URL}/schemes/?${query}`);
  if (!response.ok) throw new Error('Failed to fetch schemes');
  return response.json();
}

export async function getSchemeOptions(): Promise<SchemeOptions> {
  const response = await fetch(`${API_BASE_URL}/schemes/options/`);
  if (!response.ok) throw new Error('Failed to fetch scheme options');
  return response.json();
}
