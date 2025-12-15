#ifndef SPRITES_H
#define SPRITES_H

#include <stdint.h>

// sprite bitmaps

// These are simple 1-bit bitmaps that can be used
// for more detailed sprites. For now, we're using
// solid color rectangles in the game, but you can
// expand this to use actual bitmap data
//
// Format: Each byte represents 8 pixels
// (1 bit per pixel)
// You can create sprites using tools or by hand

// Example 16x16 player sprite (Mario-style)
static const uint8_t sprite_player[32] = {
    0b00000000, 0b00000000,
    0b00011111, 0b11111000,
    0b00111111, 0b11111100,
    0b01110011, 0b11001110,
    0b01110011, 0b11001110,
    0b00111111, 0b11111100,
    0b00011111, 0b11111000,
    0b00001111, 0b11110000,
    0b00011111, 0b11111000,
    0b00111111, 0b11111100,
    0b01111111, 0b11111110,
    0b01110000, 0b00001110,
    0b01110000, 0b00001110,
    0b00110000, 0b00001100,
    0b00011000, 0b00011000,
    0b00001111, 0b11110000,
};

// Example 12x12 enemy sprite (Goomba-style)
static const uint8_t sprite_enemy[24] = {
    0b00111111, 0b11110000,
    0b01111111, 0b11111000,
    0b11110011, 0b11001111,
    0b11110011, 0b11001111,
    0b11111111, 0b11111111,
    0b01111111, 0b11111110,
    0b01111111, 0b11111110,
    0b00111111, 0b11111100,
    0b00011111, 0b11111000,
    0b00001100, 0b00110000,
    0b00011100, 0b00111000,
    0b00111000, 0b00011100,
};

// Example 8x8 coin sprite
static const uint8_t sprite_coin[8] = {
    0b00111100,
    0b01111110,
    0b11011011,
    0b11111111,
    0b11111111,
    0b11011011,
    0b01111110,
    0b00111100,
};

// Example 8x8 coin animation frame 2
static const uint8_t sprite_coin_frame2[8] = {
    0b00011000,
    0b00111100,
    0b01011010,
    0b01111110,
    0b01111110,
    0b01011010,
    0b00111100,
    0b00011000,
};

// You can add more sprites here as needed:
// - Power-ups
// - Different enemy types
// - Particle effects
// - Background elements

#endif // SPRITES_H
