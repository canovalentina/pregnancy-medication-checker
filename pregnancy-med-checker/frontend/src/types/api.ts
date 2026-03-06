/**
 * Define typescript types for the API
 * 
 * The purpose of this file is to define the Typescript types that act as the communication contract 
 * between the frontend and backend to ensure all API requests and responses
 * have a consistent and predictable structure.
 * 
 * This helps with type safety, documentation, and easier maintenance of the API.
 * 
 * The <APIResponse<T>> type is used to define the structure of the API response.
 * The <APIError> type is used to define the structure of the API error.
 */

export type APIResponse<T> = {
  data: T;
  error: string | null;
  status: 'success' | 'error';
};

export type APIError = {
  message: string;
  status: number;
};

export type FHIRStatus = {
  status: 'connected' | 'disconnected' | 'error';
  server: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  expires_in: number;
};

export type LoginRequest = {
  username: string;
  password: string;
};

// RxNorm types
export type RxNormLookupResult = {
  query: string;
  rxcui: string[];
};

// PubMed types
export type PubMedSearchResponse = {
  ids: string[];
};

export type Publication = {
  PMID?: string;
  Title?: string;
  Abstract?: string;
  AuthorList?: string[];
  Journal?: string;
  PublicationYear?: string;
  MeSHTerms?: string[];
};

export type PubMedDetailsResponse = {
  results: Publication[];
  totalPages: number;
  totalResults: number;
};

// FHIR Patient types
export type Patient = {
  id: string;
  name: string;
  birth_date?: string;
  gender?: string;
  resource_type?: string;
};

export type PatientSummary = {
  patient: Patient | null;
  medications: any[];
  conditions: any[];
  observations: any[];
  pregnancyHistory?: {
    totalBirths: number;
    pretermBirths: number;
    pregnancies: PregnancyRecord[];
  };
};

export type PregnancyRecord = {
  id: string;
  startDate: string;
  endDate?: string;
  gestationalWeeks?: number;
  outcome?: 'birth' | 'miscarriage' | 'abortion' | 'ongoing';
  isPreterm?: boolean;
  observations: PregnancyObservation[];
};

export type PregnancyObservation = {
  id: string;
  date: string;
  type: 'gestational_age' | 'lactation' | 'other';
  value: number | string;
  unit?: string;
  trimester?: 1 | 2 | 3;
};