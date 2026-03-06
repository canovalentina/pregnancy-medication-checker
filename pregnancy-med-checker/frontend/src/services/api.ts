/**
 * Include base API client with auth headers
 */

import type { APIResponse } from '../types/api';
import { getAuthHeaders } from '../utils/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export async function get<T>(endpoint: string): Promise<APIResponse<T>> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, { headers: getAuthHeaders() });
    
    if (!response.ok) {
      return {
        data: null as unknown as T,
        error: response.statusText,
        status: 'error',
      };
    }
    
    const data = await response.json();
    return {
      data,
      error: null,
      status: 'success',
    };
  } catch (error) {
    return {
      data: null as unknown as T,
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}
