/**
 * Authentication utilities for localStorage-based auth
 */

import { User, AuthSession, LoginCredentials, SignupData, UserProfile } from '@/lib/types/auth';

const USERS_KEY = 'medsearch_users';
const SESSION_KEY = 'medsearch_session';
const SESSION_DURATION_HOURS = 24;

/**
 * Simple hash function for password storage (NOT for production use)
 * In production, use bcrypt or similar on the backend
 */
function simpleHash(password: string): string {
  let hash = 0;
  for (let i = 0; i < password.length; i++) {
    const char = password.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }
  return hash.toString(36);
}

/**
 * Validate email format
 */
export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate password strength
 * Requirements: min 8 chars, at least one uppercase, one lowercase, one number
 */
export function validatePassword(password: string): { valid: boolean; message?: string } {
  if (password.length < 8) {
    return { valid: false, message: 'Password must be at least 8 characters long' };
  }
  if (!/[A-Z]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one uppercase letter' };
  }
  if (!/[a-z]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one lowercase letter' };
  }
  if (!/[0-9]/.test(password)) {
    return { valid: false, message: 'Password must contain at least one number' };
  }
  return { valid: true };
}

/**
 * Get all users from localStorage
 */
function getUsers(): UserProfile[] {
  try {
    const stored = localStorage.getItem(USERS_KEY);
    if (!stored) return [];
    const users = JSON.parse(stored) as UserProfile[];
    return users.map((user) => ({
      ...user,
      createdAt: new Date(user.createdAt),
    }));
  } catch (error) {
    console.error('Failed to load users:', error);
    return [];
  }
}

/**
 * Save users to localStorage
 */
function saveUsers(users: UserProfile[]): void {
  try {
    localStorage.setItem(USERS_KEY, JSON.stringify(users));
  } catch (error) {
    console.error('Failed to save users:', error);
  }
}

/**
 * Sign up a new user
 */
export function signup(data: SignupData): { success: boolean; error?: string; user?: User } {
  // Validate email
  if (!validateEmail(data.email)) {
    return { success: false, error: 'Invalid email format' };
  }

  // Validate password
  const passwordValidation = validatePassword(data.password);
  if (!passwordValidation.valid) {
    return { success: false, error: passwordValidation.message };
  }

  // Check password confirmation
  if (data.password !== data.confirmPassword) {
    return { success: false, error: 'Passwords do not match' };
  }

  // Check if user already exists
  const users = getUsers();
  if (users.some((u) => u.email.toLowerCase() === data.email.toLowerCase())) {
    return { success: false, error: 'Email already registered' };
  }

  // Create new user
  const newUser: UserProfile = {
    id: `user_${Date.now()}`,
    email: data.email,
    name: data.name,
    passwordHash: simpleHash(data.password),
    createdAt: new Date(),
  };

  users.push(newUser);
  saveUsers(users);

  const user: User = {
    id: newUser.id,
    email: newUser.email,
    name: newUser.name,
    createdAt: newUser.createdAt,
  };

  return { success: true, user };
}

/**
 * Login user
 */
export function login(credentials: LoginCredentials): { success: boolean; error?: string; session?: AuthSession } {
  const users = getUsers();
  const user = users.find((u) => u.email.toLowerCase() === credentials.email.toLowerCase());

  if (!user) {
    return { success: false, error: 'Invalid email or password' };
  }

  const passwordHash = simpleHash(credentials.password);
  if (user.passwordHash !== passwordHash) {
    return { success: false, error: 'Invalid email or password' };
  }

  // Create session
  const expiresAt = new Date();
  expiresAt.setHours(expiresAt.getHours() + SESSION_DURATION_HOURS);

  const session: AuthSession = {
    user: {
      id: user.id,
      email: user.email,
      name: user.name,
      createdAt: user.createdAt,
      profilePicture: user.profilePicture,
    },
    token: `token_${Date.now()}_${Math.random().toString(36)}`,
    expiresAt,
    rememberMe: credentials.rememberMe || false,
  };

  saveSession(session);
  return { success: true, session };
}

/**
 * Save session to localStorage
 */
function saveSession(session: AuthSession): void {
  try {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  } catch (error) {
    console.error('Failed to save session:', error);
  }
}

/**
 * Get current session
 */
export function getSession(): AuthSession | null {
  try {
    const stored = localStorage.getItem(SESSION_KEY);
    if (!stored) return null;

    const session = JSON.parse(stored) as AuthSession;
    session.expiresAt = new Date(session.expiresAt);
    session.user.createdAt = new Date(session.user.createdAt);

    // Check if session expired
    if (session.expiresAt < new Date()) {
      logout();
      return null;
    }

    return session;
  } catch (error) {
    console.error('Failed to load session:', error);
    return null;
  }
}

/**
 * Logout user
 */
export function logout(): void {
  try {
    localStorage.removeItem(SESSION_KEY);
  } catch (error) {
    console.error('Failed to logout:', error);
  }
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return getSession() !== null;
}

/**
 * Get current user
 */
export function getCurrentUser(): User | null {
  const session = getSession();
  return session?.user || null;
}

/**
 * Update user profile
 */
export function updateProfile(userId: string, updates: { name?: string; profilePicture?: string }): { success: boolean; error?: string } {
  try {
    const users = getUsers();
    const userIndex = users.findIndex((u) => u.id === userId);

    if (userIndex === -1) {
      return { success: false, error: 'User not found' };
    }

    if (updates.name) {
      users[userIndex].name = updates.name;
    }
    if (updates.profilePicture !== undefined) {
      users[userIndex].profilePicture = updates.profilePicture;
    }

    saveUsers(users);

    // Update session
    const session = getSession();
    if (session && session.user.id === userId) {
      if (updates.name) session.user.name = updates.name;
      if (updates.profilePicture !== undefined) session.user.profilePicture = updates.profilePicture;
      saveSession(session);
    }

    return { success: true };
  } catch (error) {
    console.error('Failed to update profile:', error);
    return { success: false, error: 'Failed to update profile' };
  }
}

/**
 * Change password
 */
export function changePassword(userId: string, currentPassword: string, newPassword: string): { success: boolean; error?: string } {
  try {
    const users = getUsers();
    const user = users.find((u) => u.id === userId);

    if (!user) {
      return { success: false, error: 'User not found' };
    }

    // Verify current password
    const currentHash = simpleHash(currentPassword);
    if (user.passwordHash !== currentHash) {
      return { success: false, error: 'Current password is incorrect' };
    }

    // Validate new password
    const passwordValidation = validatePassword(newPassword);
    if (!passwordValidation.valid) {
      return { success: false, error: passwordValidation.message };
    }

    // Update password
    user.passwordHash = simpleHash(newPassword);
    saveUsers(users);

    return { success: true };
  } catch (error) {
    console.error('Failed to change password:', error);
    return { success: false, error: 'Failed to change password' };
  }
}

/**
 * Delete user account
 */
export function deleteAccount(userId: string): { success: boolean; error?: string } {
  try {
    const users = getUsers();
    const filteredUsers = users.filter((u) => u.id !== userId);
    saveUsers(filteredUsers);

    // Clear session
    logout();

    // Clear user-specific data
    const keysToRemove: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && (key.startsWith('medsearch_conversation_') || key === 'medsearch_conversations' || key === 'medsearch_search_history')) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach((key) => localStorage.removeItem(key));

    return { success: true };
  } catch (error) {
    console.error('Failed to delete account:', error);
    return { success: false, error: 'Failed to delete account' };
  }
}

