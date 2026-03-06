export type UserRole = 'provider' | 'patient';

export type User = {
  username: string;
  role: UserRole;
  full_name: string;
  email: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

