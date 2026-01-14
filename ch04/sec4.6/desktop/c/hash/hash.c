#include <stdio.h>
#include <string.h>
#include <stdint.h>

// Simple implementation of FNV-1a hash (better distribution than sum)
uint32_t fnv1a_hash(const char *str, size_t len) {
    uint32_t hash = 2166136261u; // FNV offset basis
    for (size_t i = 0; i < len; i++) {
        hash ^= (uint8_t)str[i];
        hash *= 16777619u; // FNV prime
    }
    return hash;
}

// Simulate HMAC-like keyed hash for integrity verification
uint32_t keyed_hash(const char *data, size_t len, const char *key) {
    // Simple keyed hash: hash(key || data || key)
    char buffer[256];
    size_t key_len = strlen(key);
    
    // Concatenate: key + data + key
    snprintf(buffer, sizeof(buffer), "%s%.*s%s", key, (int)len, data, key);
    
    return fnv1a_hash(buffer, strlen(buffer));
}

// Demonstrate collision resistance
void demonstrate_collision_resistance() {
    printf("\n-- Collision Resistance Demo --\n");
    
    const char *similar[] = {
        "IntegrityCheck",
        "IntegrityChec",
        "IntegrityChekc",
        "integritycheck"
    };
    
    printf("Similar inputs produce different hashes:\n");
    for (int i = 0; i < 4; i++) {
        uint32_t hash = fnv1a_hash(similar[i], strlen(similar[i]));
        printf("  '%s' -> 0x%08x\n", similar[i], hash);
    }
}

// Demonstrate avalanche effect (small change = large hash change)
void demonstrate_avalanche_effect() {
    printf("\n-- Avalanche Effect Demo --\n");
    printf("Single character change causes completely different hash:\n");
    
    const char *original = "The quick brown fox";
    const char *modified = "The quick brown foz"; // Only last char changed
    
    uint32_t hash1 = fnv1a_hash(original, strlen(original));
    uint32_t hash2 = fnv1a_hash(modified, strlen(modified));
    
    printf("  Original:  '%s'\n", original);
    printf("  Hash:      0x%08x (%u)\n", hash1, hash1);
    printf("  Modified:  '%s'\n", modified);
    printf("  Hash:      0x%08x (%u)\n", hash2, hash2);
    printf("  Difference in bits: %d out of 32\n", __builtin_popcount(hash1 ^ hash2));
}

// Demonstrate message authentication with keyed hash
void demonstrate_message_authentication() {
    printf("\n-- Message Authentication Demo --\n");
    
    const char *secret_key = "MySecretKey123";
    const char *message = "Transfer $1000 to Account #5678";
    
    uint32_t mac = keyed_hash(message, strlen(message), secret_key);
    
    printf("Message: %s\n", message);
    printf("MAC (Message Authentication Code): 0x%08x\n", mac);
    
    // Simulate tampering
    const char *tampered = "Transfer $9000 to Account #5678";
    uint32_t tampered_mac = keyed_hash(tampered, strlen(tampered), secret_key);
    
    printf("\nTampered Message: %s\n", tampered);
    printf("Tampered MAC: 0x%08x\n", tampered_mac);
    
    if (mac == tampered_mac) {
        printf("Success: Message verified - authentic\n");
    } else {
        printf("Fail: Authentication failed - message tampered!\n");
    }
}

int main() {
    printf("-- Cryptographic Hash Functions Demo --\n");
    printf("Using FNV-1a hash algorithm\n");
    
    // Basic integrity check
    const char *data = "IntegrityCheck";
    uint32_t hash = fnv1a_hash(data, strlen(data));
    
    printf("\n-- Basic Integrity Check --\n");
    printf("Original Data: %s\n", data);
    printf("Hash: 0x%08x (hex) = %u (decimal)\n", hash, hash);
    
    // Verify integrity
    const char *received_data = "IntegrityCheck";
    uint32_t received_hash = fnv1a_hash(received_data, strlen(received_data));
    
    printf("\nReceived Data: %s\n", received_data);
    printf("Computed Hash: 0x%08x\n", received_hash);
    
    if (hash == received_hash) {
        printf("Success: Data integrity verified - hashes match\n");
    } else {
        printf("Fail: Data corrupted - hashes don't match\n");
    }
    
    // Demonstrate with corrupted data
    const char *corrupted_data = "IntegrityChanged";
    uint32_t corrupted_hash = fnv1a_hash(corrupted_data, strlen(corrupted_data));
    
    printf("\nCorrupted Data: %s\n", corrupted_data);
    printf("Computed Hash: 0x%08x\n", corrupted_hash);
    
    if (hash == corrupted_hash) {
        printf("Success: Data integrity verified\n");
    } else {
        printf("Fail: Data integrity compromised!\n");
    }
    
    // Additional demonstrations
    demonstrate_avalanche_effect();
    demonstrate_collision_resistance();
    demonstrate_message_authentication();
    
    printf("\n-- Key Properties of Cryptographic Hashes --\n");
    printf("1. Deterministic: Same input always produces same hash\n");
    printf("2. Fast computation: Quick to compute hash value\n");
    printf("3. Avalanche effect: Small input change = large hash change\n");
    printf("4. One-way: Cannot reverse hash to get original data\n");
    printf("5. Collision resistant: Hard to find two inputs with same hash\n");
    
    return 0;
}

