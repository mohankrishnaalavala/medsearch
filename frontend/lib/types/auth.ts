/**
 * Authentication type definitions
 */

export interface User {
  id: string;
  email: string;
  name: string;
  createdAt: Date;
  profilePicture?: string;
}

export interface AuthSession {
  user: User;
  token: string;
  expiresAt: Date;
  rememberMe: boolean;
}

export interface LoginCredentials {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface SignupData {
  email: string;
  password: string;
  confirmPassword: string;
  name: string;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  passwordHash: string;
  createdAt: Date;
  profilePicture?: string;
}

