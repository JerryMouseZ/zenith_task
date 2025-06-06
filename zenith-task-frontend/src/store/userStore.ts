import { create } from 'zustand';
import { User } from '@/types/api';
import { getAuthToken, setAuthToken as persistToken, apiClient } from '@/lib/apiClient'; // apiClient also imported

interface UserState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean; // For async actions like fetching user profile
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void; // Renamed from persistToken in interface for clarity
  checkAuth: () => Promise<void>; // Check token and fetch user profile
  logout: () => Promise<void>;
}

export const useUserStore = create<UserState>((set, get) => ({
  user: null,
  token: null, // Initialize from storage on load (see checkAuth or explicit call)
  isAuthenticated: false,
  isLoading: true, // Start with loading true until first auth check

  setUser: (user) => {
    set({ user, isAuthenticated: !!user, isLoading: false });
  },

  setToken: (newTokenValue) => { // Parameter renamed to avoid conflict with imported persistToken
    persistToken(newTokenValue); // Persist token to localStorage via apiClient's helper
    set({ token: newTokenValue, isAuthenticated: !!newTokenValue });
  },

  checkAuth: async () => {
    set({ isLoading: true });
    const currentToken = getAuthToken(); // Get token from localStorage via apiClient
    if (currentToken) {
      // We need to ensure the token in the store is updated *before* making API calls
      // if it wasn't already set (e.g. on initial load)
      if (get().token !== currentToken) {
        set({ token: currentToken, isAuthenticated: true });
      } else {
        set({ isAuthenticated: true }); // Token already set, just confirm auth status
      }

      try {
        // If token exists, try to fetch user profile
        // This assumes your apiClient is set up to automatically use the token
        const userProfile = await apiClient.get<User>('/users/me'); // Make sure this endpoint is correct
        set({ user: userProfile, isAuthenticated: true, isLoading: false });
      } catch (error) {
        console.error('Failed to fetch user profile:', error);
        // Token might be invalid or expired
        persistToken(null); // Clear invalid token
        set({ user: null, token: null, isAuthenticated: false, isLoading: false });
      }
    } else {
      set({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  },

  logout: async () => {
    // Optionally call backend logout if it exists and you want to invalidate server-side session/token
    // try {
    //   await apiClient.post('/auth/logout', {});
    // } catch (error) {
    //   console.warn('Backend logout failed or not implemented:', error);
    // }
    persistToken(null); // Clear token from localStorage
    set({ user: null, token: null, isAuthenticated: false, isLoading: false });
  },
}));

// Initialize auth state when store is created/loaded on client side
// This ensures that checkAuth is called once when the app loads.
if (typeof window !== 'undefined') {
  useUserStore.getState().checkAuth();
}
