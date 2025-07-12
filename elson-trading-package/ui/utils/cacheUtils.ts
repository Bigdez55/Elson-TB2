// Frontend Cache Management Utilities

export interface CacheItem<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

export interface CacheConfig {
  defaultTTL: number; // Time to live in milliseconds
  maxSize?: number; // Maximum number of items in cache
  namespace?: string; // Optional namespace for this cache
}

export interface StorageManager {
  getItem: (key: string) => string | null;
  setItem: (key: string, value: string) => void;
  removeItem: (key: string) => void;
}

/**
 * Default cache configuration
 */
const DEFAULT_CACHE_CONFIG: CacheConfig = {
  defaultTTL: 5 * 60 * 1000, // 5 minutes
  maxSize: 100,
  namespace: 'elson_app_cache'
};

/**
 * In-memory storage implementation for environments without localStorage
 */
class InMemoryStorage implements StorageManager {
  private storage: Record<string, string> = {};

  getItem(key: string): string | null {
    return this.storage[key] || null;
  }

  setItem(key: string, value: string): void {
    this.storage[key] = value;
  }

  removeItem(key: string): void {
    delete this.storage[key];
  }
}

/**
 * Cache Manager for handling client-side caching
 */
export class CacheManager<T = any> {
  private config: CacheConfig;
  private storage: StorageManager;
  private cache: Map<string, CacheItem<T>> = new Map();
  private keysQueue: string[] = [];

  constructor(config: Partial<CacheConfig> = {}, storageType: 'localStorage' | 'memory' = 'localStorage') {
    this.config = { ...DEFAULT_CACHE_CONFIG, ...config };
    
    // Initialize storage based on availability and preference
    if (storageType === 'localStorage' && typeof window !== 'undefined' && window.localStorage) {
      this.storage = {
        getItem: (key: string) => localStorage.getItem(key),
        setItem: (key: string, value: string) => localStorage.setItem(key, value),
        removeItem: (key: string) => localStorage.removeItem(key)
      };
    } else {
      this.storage = new InMemoryStorage();
    }
    
    // Initialize cache from storage
    this.loadFromStorage();
    
    // Start cache cleanup routine
    this.setupCleanupInterval();
  }

  /**
   * Get a cached item by key
   * @param key - The cache key
   * @param forceRefresh - Whether to ignore the cache
   * @returns The cached data or undefined if not found
   */
  get(key: string, forceRefresh = false): T | undefined {
    const normalizedKey = this.normalizeKey(key);
    
    // Return undefined if forceRefresh is true
    if (forceRefresh) {
      return undefined;
    }
    
    // Check if in memory cache first (faster)
    const cacheItem = this.cache.get(normalizedKey);
    if (cacheItem && this.isValid(cacheItem)) {
      // Update access order for LRU eviction
      this.refreshKey(normalizedKey);
      return cacheItem.data;
    }
    
    // If not in memory, check storage
    try {
      const storedItem = this.storage.getItem(this.getStorageKey(normalizedKey));
      if (storedItem) {
        const parsedItem: CacheItem<T> = JSON.parse(storedItem);
        if (this.isValid(parsedItem)) {
          // Add to memory cache for faster access next time
          this.cache.set(normalizedKey, parsedItem);
          this.refreshKey(normalizedKey);
          return parsedItem.data;
        } else {
          // Clean up expired item from storage
          this.remove(normalizedKey);
        }
      }
    } catch (error) {
      console.error('Error retrieving from cache storage:', error);
      // Clean up potentially corrupted item
      this.remove(normalizedKey);
    }
    
    return undefined;
  }

  /**
   * Set a cached item
   * @param key - The cache key
   * @param data - The data to cache
   * @param ttl - Optional specific TTL for this item
   * @returns void
   */
  set(key: string, data: T, ttl?: number): void {
    const normalizedKey = this.normalizeKey(key);
    const timestamp = Date.now();
    const expiresAt = timestamp + (ttl || this.config.defaultTTL);
    
    const cacheItem: CacheItem<T> = {
      data,
      timestamp,
      expiresAt
    };
    
    // Add to memory cache
    this.cache.set(normalizedKey, cacheItem);
    this.refreshKey(normalizedKey);
    
    // Ensure we don't exceed maxSize
    this.enforceMaxSize();
    
    // Save to storage
    try {
      this.storage.setItem(
        this.getStorageKey(normalizedKey),
        JSON.stringify(cacheItem)
      );
    } catch (error) {
      console.error('Error saving to cache storage:', error);
    }
  }

  /**
   * Check if a key exists in the cache
   * @param key - The cache key
   * @returns boolean indicating if the key exists and is valid
   */
  has(key: string): boolean {
    const normalizedKey = this.normalizeKey(key);
    
    // Check memory cache first
    const memItem = this.cache.get(normalizedKey);
    if (memItem && this.isValid(memItem)) {
      return true;
    }
    
    // If not in memory, check storage
    try {
      const storedItem = this.storage.getItem(this.getStorageKey(normalizedKey));
      if (storedItem) {
        const parsedItem: CacheItem<T> = JSON.parse(storedItem);
        return this.isValid(parsedItem);
      }
    } catch (error) {
      console.error('Error checking cache storage:', error);
    }
    
    return false;
  }

  /**
   * Remove an item from the cache
   * @param key - The cache key
   */
  remove(key: string): void {
    const normalizedKey = this.normalizeKey(key);
    
    // Remove from memory cache
    this.cache.delete(normalizedKey);
    this.keysQueue = this.keysQueue.filter(k => k !== normalizedKey);
    
    // Remove from storage
    try {
      this.storage.removeItem(this.getStorageKey(normalizedKey));
    } catch (error) {
      console.error('Error removing from cache storage:', error);
    }
  }

  /**
   * Clear all cached items
   */
  clear(): void {
    // Clear memory cache
    this.cache.clear();
    this.keysQueue = [];
    
    // Attempt to clear storage items
    // We only clear items with our namespace to avoid affecting other app data
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        // If we have access to the localStorage object, we can use it to iterate through all keys
        for (let i = localStorage.length - 1; i >= 0; i--) {
          const key = localStorage.key(i);
          if (key && key.startsWith(`${this.config.namespace}:`)) {
            localStorage.removeItem(key);
          }
        }
      }
    } catch (error) {
      console.error('Error clearing cache storage:', error);
    }
  }

  /**
   * Checks if a cache item is still valid
   * @param item - The cache item to check
   * @returns boolean indicating if the item is still valid
   */
  private isValid(item: CacheItem<T>): boolean {
    return item.expiresAt > Date.now();
  }

  /**
   * Enforces the maximum cache size by removing least recently used items
   */
  private enforceMaxSize(): void {
    if (!this.config.maxSize || this.keysQueue.length <= this.config.maxSize) {
      return;
    }
    
    // Remove oldest items until we're under maxSize
    while (this.keysQueue.length > this.config.maxSize) {
      const oldestKey = this.keysQueue.shift();
      if (oldestKey) {
        this.cache.delete(oldestKey);
        try {
          this.storage.removeItem(this.getStorageKey(oldestKey));
        } catch (error) {
          console.error('Error removing oldest item from cache:', error);
        }
      }
    }
  }

  /**
   * Refresh a key's position in the LRU queue
   * @param key - The key to refresh
   */
  private refreshKey(key: string): void {
    this.keysQueue = this.keysQueue.filter(k => k !== key);
    this.keysQueue.push(key);
  }

  /**
   * Normalize a key string to ensure consistent format
   * @param key - The key to normalize
   * @returns Normalized key string
   */
  private normalizeKey(key: string): string {
    // Sanitize key to avoid any storage issues
    return key.replace(/[^a-zA-Z0-9_-]/g, '_').toLowerCase();
  }

  /**
   * Get the storage key with namespace
   * @param key - The normalized key
   * @returns Full storage key with namespace
   */
  private getStorageKey(key: string): string {
    return `${this.config.namespace}:${key}`;
  }

  /**
   * Load cached items from storage to memory
   */
  private loadFromStorage(): void {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        // Only attempt to load if we have localStorage access
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i);
          if (key && key.startsWith(`${this.config.namespace}:`)) {
            const normalizedKey = key.substring((this.config.namespace + ':').length);
            const storedItem = localStorage.getItem(key);
            
            if (storedItem) {
              try {
                const parsedItem: CacheItem<T> = JSON.parse(storedItem);
                if (this.isValid(parsedItem)) {
                  this.cache.set(normalizedKey, parsedItem);
                  this.keysQueue.push(normalizedKey);
                } else {
                  // Remove expired items during initialization
                  localStorage.removeItem(key);
                }
              } catch (parseError) {
                // Remove corrupted items
                localStorage.removeItem(key);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Error loading cache from storage:', error);
    }
  }

  /**
   * Set up an interval to clean expired items
   */
  private setupCleanupInterval(): void {
    if (typeof window !== 'undefined') {
      // Run cleanup every minute
      const cleanup = () => {
        // Clean memory cache
        for (const [key, item] of this.cache.entries()) {
          if (!this.isValid(item)) {
            this.remove(key);
          }
        }
      };
      
      // Initial cleanup
      cleanup();
      
      // Set interval for periodic cleanup
      setInterval(cleanup, 60000);
    }
  }
}

// Create and export default cache instances for different data types
export const marketDataCache = new CacheManager<any>({ 
  namespace: 'elson_market_data',
  defaultTTL: 30 * 1000, // 30 seconds
  maxSize: 200
});

export const portfolioCache = new CacheManager<any>({
  namespace: 'elson_portfolio_data',
  defaultTTL: 60 * 1000, // 1 minute
  maxSize: 50
});

export const companyProfileCache = new CacheManager<any>({
  namespace: 'elson_company_profiles',
  defaultTTL: 24 * 60 * 60 * 1000, // 24 hours
  maxSize: 100
});

export const historicalDataCache = new CacheManager<any>({
  namespace: 'elson_historical_data',
  defaultTTL: 60 * 60 * 1000, // 1 hour
  maxSize: 50
});

// Helper function to generate cache keys
export const generateCacheKey = (base: string, params: Record<string, any> = {}): string => {
  const paramString = Object.entries(params)
    .filter(([_, value]) => value !== undefined && value !== null)
    .map(([key, value]) => `${key}=${value}`)
    .sort()
    .join('&');
    
  return paramString ? `${base}:${paramString}` : base;
};