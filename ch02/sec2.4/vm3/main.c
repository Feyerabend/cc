#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "vm3.h"

//int DATA = 8192;
int MAXPROGLEN = 32768;
int* program;

void allocateprogram() {
    program = (int*) malloc(MAXPROGLEN * sizeof(int));
}

long fsize(FILE* file) {
    fseek(file, 0L, SEEK_END);
    long size = ftell(file);
    rewind(file);
    return size;
}

char* read(char *path) {
    FILE* file;
    file = fopen(path, "rb");
    if (file == NULL) {
        fprintf(stderr, "cannot open %s\n", path);
        exit(1);
    }
    long size = fsize(file);
    char* buf = (char*) calloc(1, size + 1);
    fread(buf, size, 1, file);
    fclose(file);
    return buf;
}

void exec(int* code, int start) {
	VM* vm = newVM(code, start);
	if (vm != NULL) {
		run(vm);
		freeVM(vm);
	}
}

int main(int argc, char *argv[]) {
	if (argc < 2) {
		fprintf(stderr, "usage: %s <machine code file>\n", argv[0]);
		return 1;
	}
	printf("loading ..\n");

	// get the machine code file
	char* source = read(argv[1]);
	allocateprogram();

	// parse numbers separated by comma
	const char s[2] = ",";
	char *token;
  	token = strtok(source, s);

  	// header
	int start = atoi(token);

	// body
	int i = 0;
	token = strtok(NULL, s);
	while (token != NULL) {
		program[i] = atoi(token);
		token = strtok(NULL, s);
		i++;
	}

    // print program
	printf("code ..\r");
	printf("%d:\r", start);
	int j = 0;
	do {
		printf("%d\r", program[j]);
		j++;
	}
	while (j < i);
	printf("code length = %d \n", i);

	printf("running ..\n");
	printf("- - - - - - - - - - - -\n");
	clock_t t;
	t = clock();
	exec(program, start);
	t = clock() - t;
	printf("- - - - - - - - - - - -\n");
	double duration = ((double) t) / CLOCKS_PER_SEC;
	printf("duration %f seconds\n", duration);
	printf("done running.\n");

	return 0;
}
