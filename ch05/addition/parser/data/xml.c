#include <stdio.h>
#include <string.h>
#include <ctype.h>

#define MAX_TAG_LEN 256
#define MAX_ATTR_LEN 256
#define MAX_VAL_LEN 1024

typedef struct {
    char name[MAX_ATTR_LEN];
    char value[MAX_VAL_LEN];
} Attribute;

typedef struct {
    char name[MAX_TAG_LEN];
    Attribute attributes[10];
    int attr_count;
} Tag;

void trim_whitespace(char* str) {
    char* end;

    // leading space
    while (isspace((unsigned char)*str)) str++;

    if (*str == 0) return; // ..spaces

    // trailing space
    end = str + strlen(str) - 1;
    while (end > str && isspace((unsigned char)*end))
        end--;

    // new null terminator
    *(end + 1) = 0;
}

int parse_tag(char* xml, Tag* tag) {
    char* ptr = xml;
    int inside_tag = 0;
    int attr_idx = 0;

    while (*ptr) {
        if (*ptr == '<') {
            inside_tag = 1;
            ptr++;
            char* tag_start = ptr;
            while (*ptr && *ptr != ' ' && *ptr != '>' && *ptr != '/') ptr++;
            strncpy(tag->name, tag_start, ptr - tag_start);
            tag->name[ptr - tag_start] = '\0';
        }

        if (inside_tag && *ptr == ' ') {
            ptr++;
            while (*ptr != '>' && *ptr != '/') {
                char* attr_start = ptr;
                while (*ptr && *ptr != '=' && *ptr != '>') ptr++;
                strncpy(tag->attributes[attr_idx].name, attr_start, ptr - attr_start);
                tag->attributes[attr_idx].name[ptr - attr_start] = '\0';
                
                ptr += 2; // skip = and starting " (' not impl.)
                char* val_start = ptr;
                while (*ptr && *ptr != '"') ptr++;
                strncpy(tag->attributes[attr_idx].value, val_start, ptr - val_start);
                tag->attributes[attr_idx].value[ptr - val_start] = '\0';
                tag->attr_count++;
                attr_idx++;
                ptr++;
                while (*ptr == ' ') ptr++;  // simple skip
            }
        }

        if (*ptr == '>') {
            inside_tag = 0;
            return ptr - xml + 1;
        }
        ptr++;
    }

    return 0;
}

void parse_xml(char* xml) {
    Tag tag;
    int idx = 0;

    while (xml[idx] != '\0') {
        if (xml[idx] == '<' && xml[idx + 1] != '/') {  // opening tag
            memset(&tag, 0, sizeof(Tag));
            int tag_len = parse_tag(&xml[idx], &tag);
            printf("Tag: %s\n", tag.name);

            for (int i = 0; i < tag.attr_count; i++) {
                printf("  Attribute: %s = \"%s\"\n", tag.attributes[i].name, tag.attributes[i].value);
            }
            idx += tag_len;
        } else if (xml[idx] == '<' && xml[idx + 1] == '/') {  // closing tag
            idx += 2;
            while (xml[idx] != '>') idx++;
            idx++;
        } else {
            idx++;
        }
    }
}

int main() {
    char xml_data[] = "<book title=\"C Programming\" author=\"Dennis Ritchie\" year=\"1972\"></book>";

    parse_xml(xml_data);
    return 0;
}
