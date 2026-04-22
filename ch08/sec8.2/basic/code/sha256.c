#include <openssl/evp.h>
#include <stdio.h>
#include <string.h>

void print_sha256(const char *msg) {
    EVP_MD_CTX *ctx = EVP_MD_CTX_new();
    unsigned char digest[EVP_MAX_MD_SIZE];
    unsigned int  len = 0;

    EVP_DigestInit_ex(ctx, EVP_sha256(), NULL);
    EVP_DigestUpdate(ctx, msg, strlen(msg));
    EVP_DigestFinal_ex(ctx, digest, &len);
    EVP_MD_CTX_free(ctx);

    for (unsigned int i = 0; i < len; i++)
        printf("%02x", digest[i]);
    printf("\n");
}
