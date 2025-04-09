#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define SEP 0x01
#define FORMAT_START 0x03
#define FORMAT_END 0x00
#define DOUBLE_STAR 0x09

void free_parsed_route(char *parsed) {
    free(parsed);
}

// Helper function to write an Exact component to the output buffer
static void write_exact(const char *value, size_t value_len, char **output, size_t *output_len) {
    memcpy(*output, value, value_len);
    *output += value_len;
    **output = SEP;
    (*output)++;
    *output_len += value_len + 1;
}

// Helper function to write a Format component to the output buffer
static void write_format(const char *name, size_t name_len, size_t minl, size_t maxl, int ignore_sep, char **output, size_t *output_len) {
    // Write FORMAT_START marker
    **output = FORMAT_START;
    (*output)++;
    *output_len += 1;

    // Write the name
    memcpy(*output, name, name_len);
    *output += name_len;
    **output = FORMAT_END;
    (*output)++;
    *output_len += name_len + 1;

    // Write minl and maxl as size_t values
    memcpy(*output, &minl, sizeof(size_t));
    *output += sizeof(size_t);
    memcpy(*output, &maxl, sizeof(size_t));
    *output += sizeof(size_t);
    *output_len += 2 * sizeof(size_t);

    // Write ignore_sep as a single byte
    **output = (char)ignore_sep;
    (*output)++;
    **output = SEP;
    (*output)++;
    *output_len += 2;
}

// Main parsing function
char *parse_route(const char *route, size_t route_len, size_t *output_len) {
    char *output = malloc(route_len * 8); // Allocate enough space for the output
    if (!output) return NULL;
    char *output_start = output;
    *output_len = 0;

    const char *p = route;
    const char *end = route + route_len;

    while (p < end) {
        if (*p == '/') {
            // Skip leading slashes
            write_exact("/", 1, &output, output_len);
            p++;
            continue;
        } else if (*p == '{') {
            // Handle Format component
            const char *start = p + 1; // Skip '{'
            const char *end_brace = memchr(start, '}', end - start);
            if (!end_brace) break; // Invalid format, stop parsing

            // Extract name and constraints
            const char *colon = memchr(start, ':', end_brace - start);
            size_t name_len = colon ? (size_t)(colon - start) : (size_t)(end_brace - start);
            const char *name = start;
            size_t minl = 0, maxl = (size_t)-1, ignore_sep = 0;

            if (colon) {
                const char *constraint = colon + 1;
                if (memchr(constraint, '-', end_brace - constraint)) {
                    // Parse "minl-maxl"
                    sscanf(constraint, "%zu-%zu", &minl, &maxl);
                } else {
                    // Parse "minl" (fixed length)
                    sscanf(constraint, "%zu", &minl);
                    maxl = minl;
                }
            }

            // Write the Format component
            write_format(name, name_len, minl, maxl, ignore_sep, &output, output_len);

            p = end_brace + 1; // Move past '}'
        } else if (*p == '*' && *(p + 1) == '*') {
            // Handle "**" as a special marker (\x09)
            *output = DOUBLE_STAR;
            output++;
            *output = SEP;
            output++;
            *output_len += 2;
            p += 2; // Move past "**"
        } else {
            // Handle Exact component
            const char *next_slash = memchr(p, '/', end - p);
            size_t segment_len = next_slash ? (size_t)(next_slash - p) : (size_t)(end - p);
            write_exact(p, segment_len, &output, output_len);
            p += segment_len;
        }
    }

    // Null-terminate the output
    *output = '\0';
    *output_len += 1;

    return output_start;
}

// // Example usage
// int main() {
//     const char *route = "/foo/{n:5}/bar/**/baz";
//     size_t route_len = strlen(route);
//     size_t output_len;

//     char *result = parse_route(route, route_len, &output_len);
//     if (!result) {
//         fprintf(stderr, "Memory allocation failed\n");
//         return 1;
//     }

//     printf("Parsed result (%zu bytes):\n", output_len);
//     for (size_t i = 0; i < output_len; i++) {
//         if (result[i] == SEP) {
//             printf("\\x01");
//         } else if (result[i] == FORMAT_START) {
//             printf("\\x03");
//         } else if (result[i] == FORMAT_END) {
//             printf("\\x00");
//         } else if (result[i] == DOUBLE_STAR) {
//             printf("\\x09");
//         } else {
//             printf("%c", result[i]);
//         }
//     }
//     printf("\n");

//     free(result);
//     return 0;
// }
