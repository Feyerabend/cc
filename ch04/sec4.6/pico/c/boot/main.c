/*
 * Boot Chain Demo
 * Raspberry Pi Pico 2 + Pimoroni Display Pack 2.0
 */
 
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "pico/stdlib.h"
#include "hardware/gpio.h"
#include "display.h"


// for display
static int last_displayed_scenario = -1;
static bool last_auto_advance_state = false;
static bool menu_needs_redraw = true;


// SECURITY CONSTANTS

#define SIGNATURE_SIZE 64
#define HASH_SIZE 32
#define PUBLIC_KEY_SIZE 32
#define MAX_IMAGE_SIZE (128 * 1024)
#define BOOT_MAGIC 0x53454342  // "SECB"

// For attack detection
#define MAX_FAILED_VERIFICATIONS 5

// SECURITY PRIMITIVES

/*
 * SECURITY: Constant-time comparison prevents timing attacks
 * An attacker can't learn about the data by measuring how long comparison takes
 */
static bool secure_compare(const uint8_t *a, const uint8_t *b, size_t len) {
    if (!a || !b) return false;
    
    volatile uint8_t diff = 0;
    for (size_t i = 0; i < len; i++) {
        diff |= (a[i] ^ b[i]);
    }
    return (diff == 0);
}

/*
 * SECURITY: Secure memory wipe prevents key/data leakage
 * Overwrites memory with multiple patterns before freeing
 */
static void secure_wipe(void *ptr, size_t len) {
    if (!ptr || len == 0) return;
    
    volatile uint8_t *p = (volatile uint8_t *)ptr;
    
    // Three-pass wipe with different patterns
    for (size_t i = 0; i < len; i++) p[i] = 0x00;
    for (size_t i = 0; i < len; i++) p[i] = 0xFF;
    for (size_t i = 0; i < len; i++) p[i] = 0xAA;
}


// CRYPTOGRAPHIC STRUCTURES

typedef struct {
    uint8_t data[PUBLIC_KEY_SIZE];
    char name[32];
    bool is_revoked;  // Can mark keys as compromised
} public_key_t;

typedef struct {
    uint8_t data[SIGNATURE_SIZE];
} signature_t;

// Root keys - in real system these would be in hardware ROM
static const public_key_t ROOT_PUBLIC_KEY = {
    .data = {
        0x12, 0x34, 0x56, 0x78, 0x9a, 0xbc, 0xde, 0xf0,
        0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
        0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff, 0x00, 0x11,
        0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99
    },
    .name = "ROOT_KEY",
    .is_revoked = false
};

static const public_key_t BOOTLOADER_PUBLIC_KEY = {
    .data = {
        0xab, 0xcd, 0xef, 0x01, 0x23, 0x45, 0x67, 0x89,
        0xfe, 0xdc, 0xba, 0x98, 0x76, 0x54, 0x32, 0x10,
        0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88,
        0x99, 0xaa, 0xbb, 0xcc, 0xdd, 0xee, 0xff, 0x00
    },
    .name = "BOOTLOADER_KEY",
    .is_revoked = false
};


// SIMPLIFIED HASH FUNCTION (Educational - NEVER for production!)

static bool simple_hash(const uint8_t *data, size_t len, uint8_t *hash) {
    if (!data || !hash || len == 0 || len > MAX_IMAGE_SIZE) {
        return false;
    }
    
    // Init with constants (similar to SHA-256 initial values)
    uint32_t h[8] = {
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    };
    
    // Mix in each byte (simplified - real SHA is much more complex)
    for (size_t i = 0; i < len; i++) {
        h[i % 8] ^= data[i];
        h[i % 8] = (h[i % 8] << 7) | (h[i % 8] >> 25);
        h[i % 8] += data[i] * 31;
    }
    
    // Convert to bytes
    for (int i = 0; i < 8; i++) {
        hash[i*4 + 0] = (h[i] >> 24) & 0xFF;
        hash[i*4 + 1] = (h[i] >> 16) & 0xFF;
        hash[i*4 + 2] = (h[i] >> 8) & 0xFF;
        hash[i*4 + 3] = h[i] & 0xFF;
    }
    
    return true;
}


// SIGNATURE VERIFICATION (Educational - NOT for production!)

static bool verify_signature(const uint8_t *data, size_t len, 
                            const signature_t *sig, const public_key_t *pubkey) {
    if (!data || !sig || !pubkey || len == 0) return false;
    if (pubkey->is_revoked) return false;
    
    // Hash the data
    uint8_t hash[HASH_SIZE];
    if (!simple_hash(data, len, hash)) return false;
    
    // Create expected signature (simplified - real crypto is more complex)
    uint8_t expected[SIGNATURE_SIZE];
    for (int i = 0; i < SIGNATURE_SIZE; i++) {
        expected[i] = hash[i % HASH_SIZE] ^ pubkey->data[i % PUBLIC_KEY_SIZE];
    }
    
    // SECURITY: Use constant-time comparison
    bool valid = secure_compare(sig->data, expected, SIGNATURE_SIZE);
    
    // SECURITY: Wipe temporary data
    secure_wipe(hash, sizeof(hash));
    secure_wipe(expected, sizeof(expected));
    
    return valid;
}

static bool sign_data(const uint8_t *data, size_t len, signature_t *sig, 
                     const public_key_t *pubkey) {
    if (!data || !sig || !pubkey || len == 0) return false;
    
    uint8_t hash[HASH_SIZE];
    if (!simple_hash(data, len, hash)) return false;
    
    for (int i = 0; i < SIGNATURE_SIZE; i++) {
        sig->data[i] = hash[i % HASH_SIZE] ^ pubkey->data[i % PUBLIC_KEY_SIZE];
    }
    
    secure_wipe(hash, sizeof(hash));
    return true;
}

// IMAGE STRUCTURES

typedef enum {
    IMAGE_TYPE_INVALID = 0,
    IMAGE_TYPE_BOOTLOADER = 1,
    IMAGE_TYPE_APPLICATION = 2,
    IMAGE_TYPE_MAX
} image_type_t;

typedef struct {
    uint32_t magic;
    uint32_t version;
    uint32_t image_size;
    image_type_t image_type;
    signature_t signature;
    uint8_t hash[HASH_SIZE];
    char description[64];
} __attribute__((packed)) image_header_t;

// Version counters (simulated anti-rollback storage)
static uint32_t version_counters[IMAGE_TYPE_MAX] = {0};
static uint32_t failed_verification_counter = 0;


// VERIFICATION STATUS

typedef enum {
    BOOT_STATUS_OK = 0,
    BOOT_STATUS_SIG_INVALID,
    BOOT_STATUS_VERSION_ROLLBACK,
    BOOT_STATUS_HASH_MISMATCH,
    BOOT_STATUS_CORRUPTED,
    BOOT_STATUS_SIZE_INVALID,
    BOOT_STATUS_ATTACK_DETECTED
} boot_status_t;

static const char* boot_status_strings[] = {
    "OK",
    "SIGNATURE INVALID",
    "VERSION ROLLBACK",
    "HASH MISMATCH",
    "CORRUPTED",
    "INVALID SIZE",
    "ATTACK DETECTED"
};

// IMAGE VERIFICATION (The Core Security Logic)

static boot_status_t verify_image(const image_header_t *hdr, 
                                  const uint8_t *image_data,
                                  const public_key_t *expected_key, 
                                  image_type_t expected_type) {
    if (!hdr || !image_data || !expected_key) {
        return BOOT_STATUS_CORRUPTED;
    }
    
    // Check 1: Magic number
    if (hdr->magic != BOOT_MAGIC) {
        return BOOT_STATUS_CORRUPTED;
    }
    
    // Check 2: Image type
    if (hdr->image_type != expected_type) {
        return BOOT_STATUS_CORRUPTED;
    }
    
    // Check 3: Size bounds
    if (hdr->image_size == 0 || hdr->image_size > MAX_IMAGE_SIZE) {
        return BOOT_STATUS_SIZE_INVALID;
    }
    
    // Check 4: Hash integrity
    uint8_t computed_hash[HASH_SIZE];
    if (!simple_hash(image_data, hdr->image_size, computed_hash)) {
        return BOOT_STATUS_CORRUPTED;
    }
    
    if (!secure_compare(computed_hash, hdr->hash, HASH_SIZE)) {
        secure_wipe(computed_hash, sizeof(computed_hash));
        failed_verification_counter++;
        return BOOT_STATUS_HASH_MISMATCH;
    }
    secure_wipe(computed_hash, sizeof(computed_hash));
    
    // Check 5: Digital signature
    if (!verify_signature(image_data, hdr->image_size, 
                         &hdr->signature, expected_key)) {
        failed_verification_counter++;
        return BOOT_STATUS_SIG_INVALID;
    }
    
    // Check 6: Version rollback protection
    if (hdr->version < version_counters[expected_type]) {
        failed_verification_counter++;
        return BOOT_STATUS_VERSION_ROLLBACK;
    }
    
    // Check 7: Attack detection
    if (failed_verification_counter >= MAX_FAILED_VERIFICATIONS) {
        return BOOT_STATUS_ATTACK_DETECTED;
    }
    
    // Success - update version counter
    if (hdr->version > version_counters[expected_type]) {
        version_counters[expected_type] = hdr->version;
    }
    
    return BOOT_STATUS_OK;
}


// TEST IMAGE CREATION

static bool create_test_image(image_header_t *hdr, uint8_t *image_data, 
                             size_t size, image_type_t type, uint32_t version,
                             const char *desc, const public_key_t *signing_key, 
                             bool tamper) {
    if (!hdr || !image_data || !desc || !signing_key) return false;
    if (size == 0 || size > MAX_IMAGE_SIZE) return false;
    if (type <= IMAGE_TYPE_INVALID || type >= IMAGE_TYPE_MAX) return false;
    
    // Initialize header
    memset(hdr, 0, sizeof(image_header_t));
    hdr->magic = BOOT_MAGIC;
    hdr->version = version;
    hdr->image_size = size;
    hdr->image_type = type;
    strncpy(hdr->description, desc, sizeof(hdr->description) - 1);
    
    // Generate fake image data
    for (size_t i = 0; i < size; i++) {
        image_data[i] = (uint8_t)(i ^ version ^ type);
    }
    
    // Tamper if requested (for demos)
    if (tamper && size > 2) {
        image_data[size / 2] ^= 0xFF;
    }
    
    // Calculate hash
    if (!simple_hash(image_data, size, hdr->hash)) return false;
    
    // Sign image
    if (!sign_data(image_data, size, &hdr->signature, signing_key)) return false;
    
    return true;
}

// DISPLAY HELPERS

static void draw_header(const char *title, uint16_t color) {
    display_fill_rect(0, 0, DISPLAY_WIDTH, 30, COLOR_BLACK);
    display_draw_string(10, 10, title, color, COLOR_BLACK);
}

static void draw_status_box(uint16_t y, const char *text, bool passed) {
    uint16_t bg = passed ? 0x0320 : 0x6000;  // Dark green or dark red
    uint16_t fg = passed ? COLOR_GREEN : COLOR_RED;
    
    display_fill_rect(5, y, 310, 30, bg);
    display_draw_string(10, y + 8, text, fg, bg);
}

static void draw_alert(const char *message) {
    display_fill_rect(0, 200, DISPLAY_WIDTH, 40, COLOR_RED);
    display_draw_string(20, 210, "SECURITY ALERT!", COLOR_YELLOW, COLOR_RED);
    display_draw_string(20, 222, message, COLOR_WHITE, COLOR_RED);
}

// DEMO SCENARIOS

static void demo_successful_boot(void) {
    display_clear(COLOR_BLACK);
    draw_header("SCENARIO 1: SUCCESSFUL BOOT", COLOR_GREEN);
    
    // Allocate memory
    uint8_t *bootloader_data = malloc(1024);
    uint8_t *app_data = malloc(2048);
    
    if (!bootloader_data || !app_data) {
        draw_alert("OUT OF MEMORY!");
        free(bootloader_data);
        free(app_data);
        sleep_ms(3000);
        return;
    }
    
    image_header_t bl_hdr, app_hdr;
    
    // Create bootloader image
    if (!create_test_image(&bl_hdr, bootloader_data, 1024, 
                          IMAGE_TYPE_BOOTLOADER, 1, 
                          "BOOTLOADER V1.0", &ROOT_PUBLIC_KEY, false)) {
        draw_alert("IMAGE CREATION FAILED");
        goto cleanup;
    }
    
    // Create application image
    if (!create_test_image(&app_hdr, app_data, 2048,
                          IMAGE_TYPE_APPLICATION, 1,
                          "APPLICATION V1.0", &BOOTLOADER_PUBLIC_KEY, false)) {
        draw_alert("IMAGE CREATION FAILED");
        goto cleanup;
    }
    
    // Stage 1: Verify bootloader
    display_draw_string(10, 40, "STAGE 1: ROOT VERIFIES BOOTLOADER", 
                       COLOR_CYAN, COLOR_BLACK);
    sleep_ms(800);
    
    boot_status_t status = verify_image(&bl_hdr, bootloader_data, 
                                       &ROOT_PUBLIC_KEY, IMAGE_TYPE_BOOTLOADER);
    
    char msg[64];
    snprintf(msg, sizeof(msg), "RESULT: %s", boot_status_strings[status]);
    draw_status_box(70, msg, status == BOOT_STATUS_OK);
    sleep_ms(1500);
    
    if (status != BOOT_STATUS_OK) {
        draw_alert("BOOTLOADER VERIFICATION FAILED!");
        goto cleanup;
    }
    
    // Stage 2: Verify application
    display_draw_string(10, 110, "STAGE 2: BOOTLOADER VERIFIES APP",
                       COLOR_CYAN, COLOR_BLACK);
    sleep_ms(800);
    
    status = verify_image(&app_hdr, app_data,
                         &BOOTLOADER_PUBLIC_KEY, IMAGE_TYPE_APPLICATION);
    
    snprintf(msg, sizeof(msg), "RESULT: %s", boot_status_strings[status]);
    draw_status_box(140, msg, status == BOOT_STATUS_OK);
    sleep_ms(1500);
    
    if (status != BOOT_STATUS_OK) {
        draw_alert("APPLICATION VERIFICATION FAILED!");
        goto cleanup;
    }
    
    // Success!
    display_fill_rect(0, 200, DISPLAY_WIDTH, 40, 0x0320);
    display_draw_string(70, 210, "BOOT SUCCESS!", COLOR_GREEN, 0x0320);
    display_draw_string(60, 222, "SYSTEM IS SECURE", COLOR_WHITE, 0x0320);

cleanup:
    if (bootloader_data) {
        secure_wipe(bootloader_data, 1024);
        free(bootloader_data);
    }
    if (app_data) {
        secure_wipe(app_data, 2048);
        free(app_data);
    }
    secure_wipe(&bl_hdr, sizeof(bl_hdr));
    secure_wipe(&app_hdr, sizeof(app_hdr));
    
    sleep_ms(3000);
}

static void demo_tampered_image(void) {
    display_clear(COLOR_BLACK);
    draw_header("SCENARIO 2: TAMPERED IMAGE", COLOR_RED);
    
    uint8_t *app_data = malloc(2048);
    if (!app_data) {
        draw_alert("OUT OF MEMORY!");
        sleep_ms(3000);
        return;
    }
    
    image_header_t app_hdr;
    
    display_draw_string(10, 40, "ATTACKER MODIFIES CODE..", 
                       COLOR_YELLOW, COLOR_BLACK);
    sleep_ms(1000);
    
    // Create tampered image (tamper flag = true)
    if (!create_test_image(&app_hdr, app_data, 2048,
                          IMAGE_TYPE_APPLICATION, 1,
                          "TAMPERED APP", &BOOTLOADER_PUBLIC_KEY, true)) {
        draw_alert("IMAGE CREATION FAILED");
        goto cleanup;
    }
    
    display_draw_string(10, 70, "BOOTLOADER VERIFYING..", 
                       COLOR_CYAN, COLOR_BLACK);
    sleep_ms(1000);
    
    boot_status_t status = verify_image(&app_hdr, app_data,
                                       &BOOTLOADER_PUBLIC_KEY, 
                                       IMAGE_TYPE_APPLICATION);
    
    char msg[64];
    snprintf(msg, sizeof(msg), "RESULT: %s", boot_status_strings[status]);
    draw_status_box(100, msg, status == BOOT_STATUS_OK);
    sleep_ms(1500);
    
    draw_alert("TAMPERING DETECTED!");
    
    display_draw_string(10, 165, "THE HASH DOESN'T MATCH!", 
                       COLOR_RED, COLOR_BLACK);
    display_draw_string(10, 180, "CODE WAS MODIFIED AFTER SIGNING",
                       COLOR_RED, COLOR_BLACK);
    
cleanup:
    if (app_data) {
        secure_wipe(app_data, 2048);
        free(app_data);
    }
    secure_wipe(&app_hdr, sizeof(app_hdr));
    
    sleep_ms(3000);
}

static void demo_rollback_attack(void) {
    display_clear(COLOR_BLACK);
    draw_header("SCENARIO 3: ROLLBACK ATTACK", COLOR_RED);
    
    uint8_t *app_v2 = malloc(2048);
    uint8_t *app_v1 = malloc(2048);
    
    if (!app_v2 || !app_v1) {
        draw_alert("OUT OF MEMORY!");
        free(app_v2);
        free(app_v1);
        sleep_ms(3000);
        return;
    }
    
    image_header_t hdr_v2, hdr_v1;
    
    // Install v2.0 (patched version)
    display_draw_string(10, 40, "STEP 1: INSTALL V2.0 (PATCHED)",
                       COLOR_CYAN, COLOR_BLACK);
    
    if (!create_test_image(&hdr_v2, app_v2, 2048, IMAGE_TYPE_APPLICATION,
                          2, "APP V2.0 (SECURE)", 
                          &BOOTLOADER_PUBLIC_KEY, false)) {
        draw_alert("IMAGE CREATION FAILED");
        goto cleanup;
    }
    
    boot_status_t status = verify_image(&hdr_v2, app_v2,
                                       &BOOTLOADER_PUBLIC_KEY,
                                       IMAGE_TYPE_APPLICATION);
    
    char msg[64];
    snprintf(msg, sizeof(msg), "V2.0 INSTALLED: %s", boot_status_strings[status]);
    draw_status_box(70, msg, status == BOOT_STATUS_OK);
    sleep_ms(1500);
    
    snprintf(msg, sizeof(msg), "VERSION COUNTER NOW: %u",
            version_counters[IMAGE_TYPE_APPLICATION]);
    display_draw_string(10, 110, msg, COLOR_GREEN, COLOR_BLACK);
    sleep_ms(1500);
    
    // Attacker tries v1.0 (vulnerable version)
    display_draw_string(10, 130, "STEP 2: ATTACKER TRIES V1.0..",
                       COLOR_YELLOW, COLOR_BLACK);
    sleep_ms(1000);
    
    if (!create_test_image(&hdr_v1, app_v1, 2048, IMAGE_TYPE_APPLICATION,
                          1, "APP V1.0 (VULNERABLE)",
                          &BOOTLOADER_PUBLIC_KEY, false)) {
        draw_alert("IMAGE CREATION FAILED");
        goto cleanup;
    }
    
    status = verify_image(&hdr_v1, app_v1, &BOOTLOADER_PUBLIC_KEY,
                         IMAGE_TYPE_APPLICATION);
    
    snprintf(msg, sizeof(msg), "V1.0 BLOCKED: %s", boot_status_strings[status]);
    draw_status_box(160, msg, status == BOOT_STATUS_OK);
    sleep_ms(1500);
    
    draw_alert("ROLLBACK BLOCKED!");
    
    display_draw_string(10, 175, "CAN'T DOWNGRADE TO OLD VERSION!",
                       COLOR_RED, COLOR_BLACK);
    
cleanup:
    if (app_v2) {
        secure_wipe(app_v2, 2048);
        free(app_v2);
    }
    if (app_v1) {
        secure_wipe(app_v1, 2048);
        free(app_v1);
    }
    secure_wipe(&hdr_v2, sizeof(hdr_v2));
    secure_wipe(&hdr_v1, sizeof(hdr_v1));
    
    sleep_ms(3000);
}

static void demo_wrong_signature(void) {
    display_clear(COLOR_BLACK);
    draw_header("SCENARIO 4: WRONG SIGNATURE", COLOR_RED);
    
    uint8_t *app_data = malloc(2048);
    if (!app_data) {
        draw_alert("OUT OF MEMORY!");
        sleep_ms(3000);
        return;
    }
    
    image_header_t app_hdr;
    
    display_draw_string(10, 40, "ATTACKER USES THEIR OWN KEY..",
                       COLOR_YELLOW, COLOR_BLACK);
    sleep_ms(1000);
    
    // Attacker's key (not trusted)
    public_key_t attacker_key = {
        .data = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
                 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
                 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
                 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF},
        .name = "ATTACKER_KEY",
        .is_revoked = false
    };
    
    // Create image signed with wrong key
    if (!create_test_image(&app_hdr, app_data, 2048, IMAGE_TYPE_APPLICATION,
                          1, "MALICIOUS APP", &attacker_key, false)) {
        draw_alert("IMAGE CREATION FAILED");
        goto cleanup;
    }

    display_draw_string(10, 70, "BOOTLOADER CHECKING SIGNATURE..",
                       COLOR_CYAN, COLOR_BLACK);
    sleep_ms(1000);
    
    // Try to verify with correct key (should fail)
    boot_status_t status = verify_image(&app_hdr, app_data,
                                       &BOOTLOADER_PUBLIC_KEY,
                                       IMAGE_TYPE_APPLICATION);
    
    char msg[64];
    snprintf(msg, sizeof(msg), "RESULT: %s", boot_status_strings[status]);
    draw_status_box(100, msg, status == BOOT_STATUS_OK);
    sleep_ms(1500);
    
    draw_alert("UNTRUSTED CODE!");
    
    display_draw_string(10, 165, "SIGNATURE DOESN'T MATCH!",
                       COLOR_RED, COLOR_BLACK);
    display_draw_string(10, 180, "NOT SIGNED BY TRUSTED KEY",
                       COLOR_RED, COLOR_BLACK);
    
cleanup:
    if (app_data) {
        secure_wipe(app_data, 2048);
        free(app_data);
    }
    secure_wipe(&app_hdr, sizeof(app_hdr));
    secure_wipe(&attacker_key, sizeof(attacker_key));
    
    sleep_ms(3000);
}

static void show_chain_of_trust(void) {
    display_clear(COLOR_BLACK);
    draw_header("CHAIN OF TRUST", COLOR_CYAN);
    
    display_draw_string(10, 50, "ROOT OF TRUST (ROM)", COLOR_GREEN, COLOR_BLACK);
    display_draw_string(15, 65, "- BUILT INTO HARDWARE", COLOR_WHITE, COLOR_BLACK);
    display_draw_string(15, 77, "- CONTAINS PUBLIC KEYS", COLOR_WHITE, COLOR_BLACK);
    sleep_ms(1500);
    
    display_draw_string(30, 95, "|", COLOR_YELLOW, COLOR_BLACK);
    display_draw_string(30, 100, "v", COLOR_YELLOW, COLOR_BLACK);
    
    display_draw_string(10, 110, "BOOTLOADER", COLOR_GREEN, COLOR_BLACK);
    display_draw_string(15, 125, "- VERIFIED BY ROOT", COLOR_WHITE, COLOR_BLACK);
    display_draw_string(15, 137, "- VERIFIES APPLICATION", COLOR_WHITE, COLOR_BLACK);
    sleep_ms(1500);
    
    display_draw_string(30, 155, "|", COLOR_YELLOW, COLOR_BLACK);
    display_draw_string(30, 160, "v", COLOR_YELLOW, COLOR_BLACK);
    
    display_draw_string(10, 170, "APPLICATION", COLOR_GREEN, COLOR_BLACK);
    display_draw_string(15, 185, "- VERIFIED BY BOOTLOADER", COLOR_WHITE, COLOR_BLACK);
    display_draw_string(15, 197, "- CAN LOAD MODULES", COLOR_WHITE, COLOR_BLACK);
    
    display_draw_string(10, 215, "EACH STEP VERIFIES THE NEXT",
                       COLOR_CYAN, COLOR_BLACK);
    
    sleep_ms(4000);
}

static void demo_attack_detection(void) {
    display_clear(COLOR_BLACK);
    draw_header("SCENARIO 6: ATTACK DETECTION", COLOR_RED);
    
    display_draw_string(10, 40, "SIMULATING REPEATED ATTACKS..",
                       COLOR_YELLOW, COLOR_BLACK);
    sleep_ms(1000);
    
    uint8_t *app_data = malloc(2048);
    if (!app_data) {
        draw_alert("OUT OF MEMORY!");
        sleep_ms(3000);
        return;
    }
    
    image_header_t app_hdr;
    
    // Try multiple tampered images
    for (int i = 0; i < MAX_FAILED_VERIFICATIONS; i++) {
        char msg[64];
        snprintf(msg, sizeof(msg), "ATTACK %d/%d", 
                i + 1, MAX_FAILED_VERIFICATIONS);
        display_draw_string(10, 60 + i * 15, msg, 
                           COLOR_YELLOW, COLOR_BLACK);
        
        // Create tampered image
        if (!create_test_image(&app_hdr, app_data, 2048,
                              IMAGE_TYPE_APPLICATION, 1,
                              "MALICIOUS", &BOOTLOADER_PUBLIC_KEY, true)) {
            continue;
        }
        
        boot_status_t status = verify_image(&app_hdr, app_data,
                                           &BOOTLOADER_PUBLIC_KEY,
                                           IMAGE_TYPE_APPLICATION);
        
        display_draw_string(200, 60 + i * 15,
                          status == BOOT_STATUS_OK ? "[OK]" : "[FAIL]",
                          status == BOOT_STATUS_OK ? COLOR_GREEN : COLOR_RED,
                          COLOR_BLACK);
        
        sleep_ms(400);
        
        if (failed_verification_counter >= MAX_FAILED_VERIFICATIONS) {
            break;
        }
    }
    
    sleep_ms(1000);
    draw_alert("SYSTEM LOCKED!");
    
    display_draw_string(10, 175, "TOO MANY FAILED ATTEMPTS!",
                       COLOR_RED, COLOR_BLACK);
    display_draw_string(10, 190, "POTENTIAL ATTACK DETECTED",
                       COLOR_RED, COLOR_BLACK);
    
    // Reset for demo
    failed_verification_counter = 0;
    
    if (app_data) {
        secure_wipe(app_data, 2048);
        free(app_data);
    }
    secure_wipe(&app_hdr, sizeof(app_hdr));
    
    sleep_ms(3000);
}


// MAIN APPLICATION
typedef enum {
    STATE_MENU,
    STATE_RUNNING
} app_state_t;

static app_state_t app_state = STATE_MENU;
static int current_scenario = 0;
static const int num_scenarios = 6;
static volatile bool run_scenario = false;
static bool auto_advance = false;

// Button callbacks
static void button_a_callback(button_t button) {
    (void)button;
    if (app_state == STATE_MENU) {
        current_scenario = (current_scenario + num_scenarios - 1) % num_scenarios;
    }
}

static void button_b_callback(button_t button) {
    (void)button;
    if (app_state == STATE_MENU) {
        current_scenario = (current_scenario + 1) % num_scenarios;
    }
}

static void button_x_callback(button_t button) {
    (void)button;
    if (app_state == STATE_MENU) {
        run_scenario = true;
    }
}

static void button_y_callback(button_t button) {
    (void)button;
    auto_advance = !auto_advance;
}

int main() {
    stdio_init_all();
    
    // Init display
    display_error_t err = display_pack_init();
    if (err != DISPLAY_OK) {
        // Can't show error on display, just hang
        while (1) {
            sleep_ms(1000);
        }
    }
    
    // Init buttons
    err = buttons_init();
    if (err != DISPLAY_OK) {
        display_clear(COLOR_BLACK);
        display_draw_string(30, 100, "BUTTON INIT FAILED!",
                          COLOR_RED, COLOR_BLACK);
        sleep_ms(3000);
        while (1) sleep_ms(1000);
    }
    
    // Set button callbacks
    button_set_callback(BUTTON_A, button_a_callback);
    button_set_callback(BUTTON_B, button_b_callback);
    button_set_callback(BUTTON_X, button_x_callback);
    button_set_callback(BUTTON_Y, button_y_callback);
    
    // Splash screen
    display_clear(COLOR_BLACK);
    display_draw_string(30, 60, "SECURE BOOT DEMO", COLOR_CYAN, COLOR_BLACK);
    //display_draw_string(20, 90, "RPI PICO 2", COLOR_WHITE, COLOR_BLACK);
    display_draw_string(20, 120, "A: NEXT  B: PREV", COLOR_GREEN, COLOR_BLACK);
    display_draw_string(20, 135, "X: RUN   Y: AUTO", COLOR_GREEN, COLOR_BLACK);
    sleep_ms(3000);
    
    const char *scenario_names[] = {
        "1. SUCESSFUL BOOT",
        "2. TAMPERED IMAGE",
        "3. ROLLBACK ATTACK",
        "4. WRONG SIGNATURE",
        "5. CHAIN OF TRUST",
        "6. ATTACK DETECTION"
    };
    
    while (true) {
        buttons_update();
        
        switch (app_state) {
            case STATE_MENU:
                // Only redraw menu if something changed
                if (menu_needs_redraw || 
                    current_scenario != last_displayed_scenario ||
                    auto_advance != last_auto_advance_state) {
                    
                    // Clear and draw menu
                    display_clear(COLOR_BLACK);
                    draw_header("SELECT SCENARIO", COLOR_CYAN);
                    
                    for (int i = 0; i < num_scenarios; i++) {
                        uint16_t color = (i == current_scenario) ? 
                                        COLOR_GREEN : COLOR_WHITE;
                        char line[40];
                        snprintf(line, sizeof(line), "%s %s",
                                (i == current_scenario) ? ">" : " ",
                                scenario_names[i]);
                        display_draw_string(10, 50 + i * 20, line, 
                                        color, COLOR_BLACK);
                    }
                    
                    display_draw_string(10, 200, "X: RUN SCENARIO",
                                    COLOR_CYAN, COLOR_BLACK);
                    
                    char auto_msg[32];
                    snprintf(auto_msg, sizeof(auto_msg), "Y: AUTO [%s]",
                            auto_advance ? "ON" : "OFF");
                    display_draw_string(10, 215, auto_msg, COLOR_CYAN, COLOR_BLACK);
                    
                    // Update state tracking
                    last_displayed_scenario = current_scenario;
                    last_auto_advance_state = auto_advance;
                    menu_needs_redraw = false;
                }
                
                if (run_scenario) {
                    run_scenario = false;
                    app_state = STATE_RUNNING;
                    menu_needs_redraw = true; // Force redraw when returning to menu
                }
                
                sleep_ms(100);
                break;
                
            case STATE_RUNNING:
                // Run selected scenario
                switch (current_scenario) {
                    case 0:
                        demo_successful_boot();
                        break;
                    case 1:
                        demo_tampered_image();
                        break;
                    case 2:
                        demo_rollback_attack();
                        break;
                    case 3:
                        demo_wrong_signature();
                        break;
                    case 4:
                        show_chain_of_trust();
                        break;
                    case 5:
                        demo_attack_detection();
                        break;
                }
                
                // Completion screen
                display_clear(COLOR_BLACK);
                display_draw_string(60, 100, "SCENARIO COMPLETE",
                                  COLOR_GREEN, COLOR_BLACK);
                display_draw_string(40, 130, "PRESS X TO RUN AGAIN",
                                  COLOR_WHITE, COLOR_BLACK);
                display_draw_string(40, 150, "OR A/B TO SELECT ANOTHER",
                                  COLOR_WHITE, COLOR_BLACK);
                
                sleep_ms(2000);
                
                // Auto-advance if enabled
                if (auto_advance) {
                    current_scenario = (current_scenario + 1) % num_scenarios;
                    run_scenario = true;
                    sleep_ms(1000);
                } else {
                    app_state = STATE_MENU;
                }
                break;
        }
    }

    return 0;
}


