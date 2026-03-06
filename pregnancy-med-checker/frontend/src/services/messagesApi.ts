/**
 * Messaging API client for patient-provider messaging
 */

import type { APIResponse } from '../types/api';
import { getAuthHeaders } from '../utils/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export interface Message {
  id: string;
  patient_id: string;
  sender_username: string;
  sender_role: 'patient' | 'provider';
  sender_name: string;
  content: string;
  created_at: string;
  read: boolean;
  read_at: string | null;
}

export interface MessagesResponse {
  patient_id: string;
  messages: Message[];
  total: number;
  unread_count: number;
}

export interface UnreadCountResponse {
  unread_count: number;
}

export interface PatientUnreadCountResponse {
  patient_id: string;
  unread_count: number;
}

export async function getMessages(patientId: string): Promise<APIResponse<MessagesResponse>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/messaging/patients/${patientId}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      let errorMessage = response.statusText;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || response.statusText;
      } catch {
        // If response is not JSON, use statusText
      }
      return {
        data: { patient_id: patientId, messages: [], total: 0, unread_count: 0 },
        error: errorMessage,
        status: 'error',
      };
    }
    const data: MessagesResponse = await response.json();
    return { data, error: null, status: 'success' };
  } catch (error) {
    return {
      data: { patient_id: patientId, messages: [], total: 0, unread_count: 0 },
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}

export async function sendMessage(
  patientId: string,
  content: string
): Promise<APIResponse<{ message: string; message_data: Message }>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/messaging/patients/${patientId}`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ patient_id: patientId, content }),
    });
    if (!response.ok) {
      let errorMessage = response.statusText;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || response.statusText;
      } catch {
        try {
          const errorText = await response.text();
          errorMessage = errorText || response.statusText;
        } catch {
          // Use statusText as fallback
        }
      }
      return {
        data: { message: '', message_data: {} as Message },
        error: errorMessage,
        status: 'error',
      };
    }
    const data = await response.json();
    return { data, error: null, status: 'success' };
  } catch (error) {
    return {
      data: { message: '', message_data: {} as Message },
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}

export async function getUnreadCount(): Promise<APIResponse<UnreadCountResponse>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/messaging/unread-count`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      return {
        data: { unread_count: 0 },
        error: response.statusText,
        status: 'error',
      };
    }
    const data: UnreadCountResponse = await response.json();
    return { data, error: null, status: 'success' };
  } catch (error) {
    return {
      data: { unread_count: 0 },
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}

export async function getPatientUnreadCount(
  patientId: string
): Promise<APIResponse<PatientUnreadCountResponse>> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/messaging/patients/${patientId}/unread-count`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      return {
        data: { patient_id: patientId, unread_count: 0 },
        error: response.statusText,
        status: 'error',
      };
    }
    const data: PatientUnreadCountResponse = await response.json();
    return { data, error: null, status: 'success' };
  } catch (error) {
    return {
      data: { patient_id: patientId, unread_count: 0 },
      error: error instanceof Error ? error.message : 'Unknown error',
      status: 'error',
    };
  }
}

