/*
 * vgtp.c — CRC16 and packet validation
 */

#include "vgtp.h"
#include <string.h>

/* CRC16-CCITT, polynomial 0x1021, initial value 0xFFFF */
uint16_t vgtp_crc16(const uint8_t *data, uint16_t len) {
    uint16_t crc = 0xFFFF;
    for (uint16_t i = 0; i < len; i++) {
        crc ^= (uint16_t)data[i] << 8;
        for (int j = 0; j < 8; j++) {
            if (crc & 0x8000) crc = (uint16_t)((crc << 1) ^ 0x1021);
            else              crc = (uint16_t)(crc << 1);
        }
    }
    return crc;
}

/* alternative:
uint16_t vgtp_crc16(const uint8_t *data, uint16_t len) {
    uint16_t crc = 0xFFFF;

    for (uint16_t i = 0; i < len; i++) {
        crc ^= (uint16_t)data[i] << 8;

        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x8000)
                crc = (crc << 1) ^ 0x1021;
            else
                crc <<= 1;
        }
    }

    return crc;
}*/

/*
 * Verify the CRC of a full VGTP DATA packet.
 * Convention: if the crc field in the packet is 0, skip verification
 * (useful during development / from senders that omit CRC).
 */
bool vgtp_packet_crc_ok(const uint8_t *packet, uint16_t total_len) {
    if (total_len < VGTP_HEADER_SIZE) return false;

    const vgtp_data_hdr_t *h = (const vgtp_data_hdr_t *)packet;
    if (h->crc == 0) return true;   /* skip-check convention */

    /* Compute CRC with crc field zeroed */
    uint8_t tmp[total_len];
    memcpy(tmp, packet, total_len);
    ((vgtp_data_hdr_t *)tmp)->crc = 0;

    return vgtp_crc16(tmp, total_len) == h->crc;
}
