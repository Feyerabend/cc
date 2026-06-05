#include "dssp.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/* Emit helpers */

void dssp_emit(dssp_t *d, int val)
{
    tryte_t tr = int_to_tryte(val);
    setun70_mem_write(&d->vm, d->here, &tr);
    d->here++;
}

/* Emit a 2-tryte address (lo then hi, each a tryte). */
void dssp_emit2(dssp_t *d, int addr)
{
    dssp_emit(d, addr % 243);
    dssp_emit(d, addr / 243);
}

/* Patch a 2-tryte address previously emitted with placeholder zeros. */
void dssp_patch2(dssp_t *d, int at, int addr)
{
    tryte_t lo = int_to_tryte(addr % 243);
    tryte_t hi = int_to_tryte(addr / 243);
    setun70_mem_write(&d->vm, at,     &lo);
    setun70_mem_write(&d->vm, at + 1, &hi);
}

/* Emit opcode + 2-tryte address (3 trytes total: op lo hi). */
static void emit_jmp(dssp_t *d, int op, int addr)
{
    dssp_emit(d, op);
    dssp_emit2(d, addr);
}

/* Emit CALL lo hi. */
static void emit_call(dssp_t *d, int addr)
{
    emit_jmp(d, S70_CALL, addr);
}

/* Emit PUSH <literal> (2 trytes: PUSH op + value). */
static void emit_push(dssp_t *d, int val)
{
    dssp_emit(d, S70_PUSH);
    dssp_emit(d, val);
}

void dssp_write_sysvar(dssp_t *d, int addr, int val)
{
    tryte_t tr = int_to_tryte(val);
    setun70_mem_write(&d->vm, addr, &tr);
}

int dssp_read_sysvar(const dssp_t *d, int addr)
{
    tryte_t tr = setun70_mem_read(&d->vm, addr);
    return tryte_to_int(&tr);
}

/* Dictionary building */

/*
 * Write a dict header and return the CFA address.
 * Layout: link_lo link_hi flags namelen name... <body starts here = CFA>
 */
static int begin_word(dssp_t *d, const char *name, int immediate)
{
    int prev    = d->latest;
    int namelen = (int) strlen(name);
    int hdr     = d->here;

    dssp_emit(d, prev % 243);        /* link_lo */
    dssp_emit(d, prev / 243);        /* link_hi */
    dssp_emit(d, immediate ? FLAG_IMMEDIATE : 0);
    dssp_emit(d, namelen);
    for (int i = 0; i < namelen; i++)
        dssp_emit(d, (unsigned char) name[i]);

    d->latest = hdr;
    return d->here;   /* CFA = first instruction address */
}

/* Register a primitive: write its header, record CFA in prim table. */
static int def_prim(dssp_t *d, const char *name, int immediate)
{
    int cfa = begin_word(d, name, immediate);
    if (d->nprim < MAX_PRIMS) {
        d->prims[d->nprim].name      = name;
        d->prims[d->nprim].cfa       = cfa;
        d->prims[d->nprim].immediate = immediate;
        d->nprim++;
    }
    return cfa;
}

/* Look up a primitive CFA by name (C-side, bootstrap only). */
static int prim_cfa(const dssp_t *d, const char *name)
{
    for (int i = 0; i < d->nprim; i++)
        if (strcmp(d->prims[i].name, name) == 0)
            return d->prims[i].cfa;
    fprintf(stderr, "bootstrap: unknown primitive '%s'\n", name);
    return 0;
}

/* Dictionary search */

int dssp_find(const dssp_t *d, const char *name, int *imm)
{
    int namelen = (int) strlen(name);
    int hdr     = d->latest;

    while (hdr > 0) {
        int lo       = tryte_to_int(&d->vm.mem[hdr]);
        int hi       = tryte_to_int(&d->vm.mem[hdr + 1]);
        int flags    = tryte_to_int(&d->vm.mem[hdr + 2]);
        int wlen     = tryte_to_int(&d->vm.mem[hdr + 3]);
        int prev     = lo + hi * 243;

        if (wlen == namelen) {
            int ok = 1;
            for (int i = 0; i < namelen && ok; i++)
                if (tryte_to_int(&d->vm.mem[hdr + 4 + i]) != (unsigned char) name[i])
                    ok = 0;
            if (ok) {
                if (imm) *imm = (flags & FLAG_IMMEDIATE) ? 1 : 0;
                return hdr + 4 + namelen;   /* CFA */
            }
        }

        hdr = prev;
    }
    return -1;
}

/* Host-call dispatch */

static dssp_t *g_dssp = NULL;

typedef void (*hcfn_t)(setun70_t *);
static hcfn_t hctab[S70_HC_MAX - 27 + 1];

static void hc_word(setun70_t *vm)
{
    dssp_t *d = g_dssp;
    int i     = d->toin;
    int len   = d->tiblen;

    while (i < len && d->tib[i] == ' ') i++;

    if (i >= len) {
        d->toin = i;
        tryte_t z = int_to_tryte(0);
        setun70_ds_push(vm, &z);
        return;
    }

    int start = i;
    while (i < len && d->tib[i] != ' ') i++;

    int wlen = i - start;
    if (wlen > 63) wlen = 63;
    memcpy(d->wordbuf, d->tib + start, wlen);
    d->wordbuf[wlen] = '\0';
    d->wordlen = wlen;
    d->toin    = i;

    tryte_t tr = int_to_tryte(wlen);
    setun70_ds_push(vm, &tr);
}

static void hc_find(setun70_t *vm)
{
    dssp_t *d  = g_dssp;
    int is_imm = 0;
    int cfa    = dssp_find(d, d->wordbuf, &is_imm);

    if (cfa < 0) {
        /* Not found: push 0 0 0 (lo=0, hi=0, found=0) */
        tryte_t z = int_to_tryte(0);
        setun70_ds_push(vm, &z);
        setun70_ds_push(vm, &z);
        setun70_ds_push(vm, &z);
    } else {
        dssp_write_sysvar(d, 1, is_imm);
        /* Push lo, hi, found=1 */
        tryte_t lo    = int_to_tryte(cfa % 243);
        tryte_t hi    = int_to_tryte(cfa / 243);
        tryte_t found = int_to_tryte(1);
        setun70_ds_push(vm, &lo);
        setun70_ds_push(vm, &hi);
        setun70_ds_push(vm, &found);
    }
}

static void hc_number(setun70_t *vm)
{
    dssp_t *d = g_dssp;
    char *ep;
    long val = strtol(d->wordbuf, &ep, d->base);
    int ok   = (ep != d->wordbuf && *ep == '\0') ? 1 : 0;

    tryte_t vt = int_to_tryte((int) val);
    tryte_t ot = int_to_tryte(ok);
    setun70_ds_push(vm, &vt);
    setun70_ds_push(vm, &ot);
}

static void hc_dot(setun70_t *vm)
{
    tryte_t t = setun70_ds_pop(vm);
    printf("%d ", tryte_to_int(&t));
    fflush(stdout);
}

static void hc_dottern(setun70_t *vm)
{
    tryte_t t = setun70_ds_pop(vm);
    int v     = tryte_to_int(&t);

    if (v == 0) { printf("0 "); fflush(stdout); return; }

    char buf[32];
    int  pos  = 0;
    int  sign = (v < 0) ? -1 : 1;
    int  tmp  = (v < 0) ? -v :  v;

    while (tmp > 0) {
        int rem = tmp % 3;
        if (rem == 2) { rem = -1; tmp++; }
        int digit = sign * rem;
        buf[pos++] = (digit > 0) ? '+' : (digit < 0) ? '-' : '0';
        tmp /= 3;
    }
    buf[pos] = '\0';
    for (int a = 0, b = pos - 1; a < b; a++, b--) {
        char tmp2 = buf[a]; buf[a] = buf[b]; buf[b] = tmp2;
    }
    printf("%s ", buf);
    fflush(stdout);
}

static void hc_dots(setun70_t *vm)
{
    printf("< ");
    for (int i = 0; i < vm->ds_top; i++)
        printf("%d ", tryte_to_int(&vm->ds[i]));
    printf("> ");
    fflush(stdout);
}

static void hc_execute(setun70_t *vm)
{
    dssp_t *d  = g_dssp;
    /* Pop 2-tryte CFA (hi on top, lo on bottom) */
    tryte_t hi_t = setun70_ds_pop(vm);
    tryte_t lo_t = setun70_ds_pop(vm);
    int cfa = tryte_to_int(&lo_t) + tryte_to_int(&hi_t) * 243;
    /* Push 2-tryte return address: hi first, then lo (RET pops lo first) */
    tryte_t rhi = int_to_tryte(vm->pc / 243);
    tryte_t rlo = int_to_tryte(vm->pc % 243);
    setun70_rs_push(vm, &rhi);
    setun70_rs_push(vm, &rlo);
    vm->pc = cfa;
    (void) d;
}

static void hc_compile(setun70_t *vm)
{
    dssp_t *d  = g_dssp;
    int is_imm = dssp_read_sysvar(d, 1);
    /* Pop 2-tryte CFA (hi on top, lo below) */
    tryte_t hi_t = setun70_ds_pop(vm);
    tryte_t lo_t = setun70_ds_pop(vm);
    int cfa      = tryte_to_int(&lo_t) + tryte_to_int(&hi_t) * 243;

    if (is_imm) {
        /* Execute immediately even in compile mode */
        tryte_t rhi = int_to_tryte(vm->pc / 243);
        tryte_t rlo = int_to_tryte(vm->pc % 243);
        setun70_rs_push(vm, &rhi);
        setun70_rs_push(vm, &rlo);
        vm->pc = cfa;
    } else {
        /* Emit CALL lo hi at HERE */
        tryte_t call_op = int_to_tryte(S70_CALL);
        tryte_t lo      = int_to_tryte(cfa % 243);
        tryte_t hi      = int_to_tryte(cfa / 243);
        setun70_mem_write(vm, d->here,     &call_op);
        setun70_mem_write(vm, d->here + 1, &lo);
        setun70_mem_write(vm, d->here + 2, &hi);
        d->here += 3;
    }
}

static void hc_tick(setun70_t *vm)
{
    hc_word(vm);
    tryte_t lt = setun70_ds_pop(vm);
    if (tryte_to_int(&lt) == 0) {
        /* Not found: push 0 0 */
        tryte_t z = int_to_tryte(0);
        setun70_ds_push(vm, &z);
        setun70_ds_push(vm, &z);
        return;
    }
    hc_find(vm);
}

static void hc_state_r(setun70_t *vm)
{
    dssp_t *d = g_dssp;
    tryte_t t = int_to_tryte(d->state);
    setun70_ds_push(vm, &t);
}

static void hc_state_w(setun70_t *vm)
{
    dssp_t *d  = g_dssp;
    tryte_t vt = setun70_ds_pop(vm);
    d->state   = tryte_to_int(&vt);
}

/* hc_here_r and hc_here_w are defined after build_compiler_words, below. */
static void hc_here_r(setun70_t *vm);
static void hc_here_w(setun70_t *vm);

static void hc_immpatch(setun70_t *vm)
{
    /* DS layout (top to bottom): tgt_hi tgt_lo hole_hi hole_lo
       Pop: tgt_hi, tgt_lo, hole_hi, hole_lo */
    dssp_t *d      = g_dssp;
    tryte_t tgt_hi = setun70_ds_pop(vm);
    tryte_t tgt_lo = setun70_ds_pop(vm);
    tryte_t hol_hi = setun70_ds_pop(vm);
    tryte_t hol_lo = setun70_ds_pop(vm);
    int target  = tryte_to_int(&tgt_lo) + tryte_to_int(&tgt_hi) * 243;
    int hole_at = tryte_to_int(&hol_lo) + tryte_to_int(&hol_hi) * 243;
    dssp_patch2(d, hole_at, target);
}

/* Step wrapper: intercept host-call opcodes before the VM sees them */

static void hc_comma(setun70_t *vm)
{
    dssp_t *d  = g_dssp;
    tryte_t vt = setun70_ds_pop(vm);
    int val    = tryte_to_int(&vt);
    tryte_t tr = int_to_tryte(val);
    setun70_mem_write(vm, d->here, &tr);
    d->here++;
}

static void hc_allot(setun70_t *vm)
{
    dssp_t *d  = g_dssp;
    tryte_t nt = setun70_ds_pop(vm);
    d->here   += tryte_to_int(&nt);
}

static void hc_memw2(setun70_t *vm)
{
    /* DS: val lo hi  ->  mem[lo+hi*243] = val */
    tryte_t hi_t = setun70_ds_pop(vm);
    tryte_t lo_t = setun70_ds_pop(vm);
    tryte_t val  = setun70_ds_pop(vm);
    int addr     = tryte_to_int(&lo_t) + tryte_to_int(&hi_t) * 243;
    setun70_mem_write(vm, addr, &val);
}

static void hc_memr2(setun70_t *vm)
{
    /* DS: lo hi  ->  mem[lo+hi*243] */
    tryte_t hi_t = setun70_ds_pop(vm);
    tryte_t lo_t = setun70_ds_pop(vm);
    int addr     = tryte_to_int(&lo_t) + tryte_to_int(&hi_t) * 243;
    tryte_t val  = setun70_mem_read(vm, addr);
    setun70_ds_push(vm, &val);
}

static int dssp_step(dssp_t *d)
{
    setun70_t *vm = &d->vm;
    if (vm->halted || vm->error) return -1;

    int op = tryte_to_int(&vm->mem[vm->pc]);

    if (op >= S70_HC_WORD && op < S70_HC_MAX) {
        vm->pc++;
        hcfn_t fn = hctab[op - 27];
        if (fn) fn(vm);
        return 0;
    }

    return setun70_step(vm);
}

static void dssp_run(dssp_t *d)
{
    while (!d->vm.halted && !d->vm.error)
        dssp_step(d);
}

/* Kernel bootstrap */

static void build_primitives(dssp_t *d)
{
    /* Arithmetic */
    def_prim(d, "+", 0);      dssp_emit(d, S70_ADD);  dssp_emit(d, S70_RET);
    def_prim(d, "-", 0);      dssp_emit(d, S70_SUB);  dssp_emit(d, S70_RET);
    def_prim(d, "*", 0);      dssp_emit(d, S70_MUL);  dssp_emit(d, S70_RET);
    def_prim(d, "/", 0);      dssp_emit(d, S70_DIV);  dssp_emit(d, S70_RET);
    def_prim(d, "negate", 0); dssp_emit(d, S70_NEG);  dssp_emit(d, S70_RET);
    def_prim(d, "abs", 0);    dssp_emit(d, S70_ABS);  dssp_emit(d, S70_RET);
    def_prim(d, "sgn", 0);    dssp_emit(d, S70_SGN);  dssp_emit(d, S70_RET);

    /* mod: a b -- a mod b  (= a - (a/b)*b) */
    def_prim(d, "mod", 0);
    /* DS: a b */
    dssp_emit(d, S70_OVER);  /* a b a */
    dssp_emit(d, S70_OVER);  /* a b a b */
    dssp_emit(d, S70_DIV);   /* a b q */
    dssp_emit(d, S70_MUL);   /* a q*b */
    dssp_emit(d, S70_SUB);   /* a - q*b = a mod b */
    dssp_emit(d, S70_RET);

    /* Comparisons */
    def_prim(d, "=", 0);   dssp_emit(d, S70_EQ);   dssp_emit(d, S70_RET);
    def_prim(d, "<", 0);   dssp_emit(d, S70_LT);   dssp_emit(d, S70_RET);

    def_prim(d, ">", 0);
    dssp_emit(d, S70_SWAP); dssp_emit(d, S70_LT);  dssp_emit(d, S70_RET);

    /* 0= : a -- 1 if a==0 else 0 */
    def_prim(d, "0=", 0);
    dssp_emit(d, S70_SGN);      /* -1, 0, or +1 */
    dssp_emit(d, S70_ABS);      /* 0 or 1 */
    dssp_emit(d, S70_NEG);      /* 0 or -1 */
    emit_push(d, 1);
    dssp_emit(d, S70_ADD);      /* 1 if was 0, else 0 */
    dssp_emit(d, S70_RET);

    def_prim(d, "0<", 0);
    dssp_emit(d, S70_SGN);  emit_push(d, -1);  dssp_emit(d, S70_EQ);
    dssp_emit(d, S70_RET);

    def_prim(d, "0>", 0);
    dssp_emit(d, S70_SGN);  emit_push(d, 1);   dssp_emit(d, S70_EQ);
    dssp_emit(d, S70_RET);

    /* Ternary logic (Setun-70's native min/max/negation logic) */
    def_prim(d, "and", 0); dssp_emit(d, S70_AND); dssp_emit(d, S70_RET);
    def_prim(d, "or",  0); dssp_emit(d, S70_OR);  dssp_emit(d, S70_RET);
    def_prim(d, "not", 0); dssp_emit(d, S70_NOT); dssp_emit(d, S70_RET);

    /* Stack manipulation */
    def_prim(d, "dup",   0); dssp_emit(d, S70_DUP);  dssp_emit(d, S70_RET);
    def_prim(d, "drop",  0); dssp_emit(d, S70_POP);  dssp_emit(d, S70_RET);
    def_prim(d, "swap",  0); dssp_emit(d, S70_SWAP); dssp_emit(d, S70_RET);
    def_prim(d, "over",  0); dssp_emit(d, S70_OVER); dssp_emit(d, S70_RET);
    def_prim(d, "depth", 0); dssp_emit(d, S70_DEPTH);dssp_emit(d, S70_RET);

    /* rot: a b c -- b c a */
    def_prim(d, "rot", 0);
    dssp_emit(d, S70_RPUSH);  /* RS=[c]; DS=[a b] */
    dssp_emit(d, S70_SWAP);   /* DS=[b a] */
    dssp_emit(d, S70_RPOP);   /* DS=[b a c] */
    dssp_emit(d, S70_SWAP);   /* DS=[b c a] */
    dssp_emit(d, S70_RET);

    /* -rot: a b c -- c a b */
    def_prim(d, "-rot", 0);
    dssp_emit(d, S70_SWAP);   /* a c b */
    dssp_emit(d, S70_RPUSH);  /* RS=[b] */
    dssp_emit(d, S70_SWAP);   /* DS=[c a] */
    dssp_emit(d, S70_RPOP);   /* DS=[c a b] */
    dssp_emit(d, S70_RET);

    def_prim(d, "nip",  0);
    dssp_emit(d, S70_SWAP); dssp_emit(d, S70_POP); dssp_emit(d, S70_RET);

    def_prim(d, "tuck", 0);
    dssp_emit(d, S70_SWAP); dssp_emit(d, S70_OVER); dssp_emit(d, S70_RET);

    def_prim(d, "2dup",  0);
    dssp_emit(d, S70_OVER); dssp_emit(d, S70_OVER); dssp_emit(d, S70_RET);

    def_prim(d, "2drop", 0);
    dssp_emit(d, S70_POP);  dssp_emit(d, S70_POP);  dssp_emit(d, S70_RET);

    /* Return stack */
    def_prim(d, ">r",  0); dssp_emit(d, S70_RPUSH); dssp_emit(d, S70_RET);
    def_prim(d, "r>",  0); dssp_emit(d, S70_RPOP);  dssp_emit(d, S70_RET);
    def_prim(d, "r@",  0); dssp_emit(d, S70_RPEEK); dssp_emit(d, S70_RET);

    /* Memory:  @ : addr -- val;   ! : val addr -- */
    def_prim(d, "@", 0); dssp_emit(d, S70_LOAD);  dssp_emit(d, S70_RET);
    def_prim(d, "!", 0);
    dssp_emit(d, S70_STORE);
    dssp_emit(d, S70_RET);

    /* +! : n addr -- ;  add n to value at addr */
    def_prim(d, "+!", 0);
    dssp_emit(d, S70_DUP);    /* n addr addr */
    dssp_emit(d, S70_LOAD);   /* n addr old */
    dssp_emit(d, S70_RPUSH);  /* RS=[old]; DS=[n addr] */
    dssp_emit(d, S70_SWAP);   /* DS=[addr n] */
    dssp_emit(d, S70_RPOP);   /* DS=[addr n old] */
    dssp_emit(d, S70_ADD);    /* DS=[addr n+old] */
    dssp_emit(d, S70_SWAP);   /* DS=[n+old addr] */
    dssp_emit(d, S70_STORE);  /* mem[addr] = n+old */
    dssp_emit(d, S70_RET);

    def_prim(d, "c@", 0); dssp_emit(d, S70_LOAD);  dssp_emit(d, S70_RET);
    def_prim(d, "c!", 0); dssp_emit(d, S70_STORE); dssp_emit(d, S70_RET);

    /* I/O */
    def_prim(d, "emit",  0); dssp_emit(d, S70_EMIT); dssp_emit(d, S70_RET);
    def_prim(d, "key",   0); dssp_emit(d, S70_KEY);  dssp_emit(d, S70_RET);
    def_prim(d, "cr",    0); emit_push(d, '\n'); dssp_emit(d, S70_EMIT); dssp_emit(d, S70_RET);
    def_prim(d, "space", 0); emit_push(d, ' ');  dssp_emit(d, S70_EMIT); dssp_emit(d, S70_RET);

    /* Output words (host-assisted) */
    def_prim(d, ".",  0); dssp_emit(d, S70_HC_DOT);    dssp_emit(d, S70_RET);
    def_prim(d, ".t", 0); dssp_emit(d, S70_HC_DOTTERN);dssp_emit(d, S70_RET);
    def_prim(d, ".s", 0); dssp_emit(d, S70_HC_DOTS);   dssp_emit(d, S70_RET);

    /* System state words (host-assisted) */
    def_prim(d, "execute", 0); dssp_emit(d, S70_HC_EXECUTE); dssp_emit(d, S70_RET);
    def_prim(d, "'",       0); dssp_emit(d, S70_HC_TICK);    dssp_emit(d, S70_RET);

    /* here: -- lo hi  (HERE as two trytes; address space exceeds one tryte range) */
    def_prim(d, "here", 0);
    dssp_emit(d, S70_HC_HERE_R);
    dssp_emit(d, S70_RET);

    /* allot: n --  advance HERE by n */
    def_prim(d, "allot", 0);
    dssp_emit(d, S70_HC_HERE_R);   /* n lo hi */
    emit_push(d, 243);
    dssp_emit(d, S70_MUL);         /* n lo hi*243 */
    dssp_emit(d, S70_ADD);         /* n here */
    dssp_emit(d, S70_ADD);         /* here+n */
    dssp_emit(d, S70_HC_HERE_W);
    dssp_emit(d, S70_RET);

    /* , : val --  write val at HERE and HERE++ */
    def_prim(d, ",", 0);
    dssp_emit(d, S70_HC_COMMA);   /* HC_COMMA: DS: val -> ; mem[HERE]=val, HERE++ */
    dssp_emit(d, S70_RET);

    /* bye */
    def_prim(d, "bye", 0);
    dssp_emit(d, S70_HALT);
    dssp_emit(d, S70_RET);
}

static void build_compiler_words(dssp_t *d)
{
    int comma_cfa = prim_cfa(d, ",");

    /* [ : enter interpret mode (immediate) */
    def_prim(d, "[", 1);
    emit_push(d, 0);
    dssp_emit(d, S70_HC_STATE_W);
    dssp_emit(d, S70_RET);

    /* ] : enter compile mode */
    def_prim(d, "]", 0);
    emit_push(d, 1);
    dssp_emit(d, S70_HC_STATE_W);
    dssp_emit(d, S70_RET);

    /* if (immediate): emit JZERO with a placeholder address; push the hole address on DS */
    def_prim(d, "if", 1);
    emit_push(d, S70_JZERO);
    emit_call(d, comma_cfa);             /* emit JZERO opcode */
    /* Push hole address as lo hi (2 items, not combined) */
    dssp_emit(d, S70_HC_HERE_R);        /* lo hi on DS */
    emit_push(d, 0);
    emit_call(d, comma_cfa);            /* emit lo placeholder */
    emit_push(d, 0);
    emit_call(d, comma_cfa);            /* emit hi placeholder */
    dssp_emit(d, S70_RET);

    /* then (immediate): patch the hole left by if with the current HERE */
    def_prim(d, "then", 1);
    /* DS: hole_lo hole_hi — push target HERE as lo hi, then IMMPATCH */
    dssp_emit(d, S70_HC_HERE_R);        /* hole_lo hole_hi tgt_lo tgt_hi */
    dssp_emit(d, S70_HC_IMMPATCH);      /* consumes hole_lo hole_hi tgt_lo tgt_hi */
    dssp_emit(d, S70_RET);

    /* else (immediate): patch if's hole, emit JUMP with new hole for then */
    def_prim(d, "else", 1);
    /* DS: hole1_lo hole1_hi */
    emit_push(d, S70_JUMP);
    emit_call(d, comma_cfa);            /* emit JUMP opcode */
    /* hole2 = current HERE (as lo hi) */
    dssp_emit(d, S70_HC_HERE_R);        /* hole1_lo hole1_hi hole2_lo hole2_hi */
    emit_push(d, 0);
    emit_call(d, comma_cfa);            /* emit JUMP lo placeholder */
    emit_push(d, 0);
    emit_call(d, comma_cfa);            /* emit JUMP hi placeholder */
    /* Now: DS = hole1_lo hole1_hi hole2_lo hole2_hi */
    /* Patch hole1 with current HERE:
       Need DS = hole1_lo hole1_hi here_lo here_hi for IMMPATCH
       But hole2 is in the way. Save hole2 to RS first. */
    dssp_emit(d, S70_RPUSH);           /* RS=[hole2_hi]; DS=[hole1_lo hole1_hi hole2_lo] */
    dssp_emit(d, S70_RPUSH);           /* RS=[hole2_hi,hole2_lo]; DS=[hole1_lo hole1_hi] */
    dssp_emit(d, S70_HC_HERE_R);       /* hole1_lo hole1_hi here_lo here_hi */
    dssp_emit(d, S70_HC_IMMPATCH);
    /* Restore hole2 from RS */
    dssp_emit(d, S70_RPOP);            /* hole2_lo */
    dssp_emit(d, S70_RPOP);            /* hole2_lo hole2_hi */
    dssp_emit(d, S70_RET);

    /* begin (immediate): push HERE as the loop-back address */
    def_prim(d, "begin", 1);
    dssp_emit(d, S70_HC_HERE_R);   /* push HERE as lo hi */
    dssp_emit(d, S70_RET);

    /*
     * Helper: emit-jump-to — pops loop_addr from DS, emits JUMP lo hi.
     * Used by AGAIN and REPEAT.
     */
    int emit_jump_to = d->here + 4 + (int) strlen("(ejt)");
    /* (ejt): DS = lo hi  →  emit JUMP lo hi.
       DS has hi on top, so swap before emitting. */
    def_prim(d, "(ejt)", 0);
    emit_push(d, S70_JUMP);
    emit_call(d, comma_cfa);          /* emit JUMP opcode */
    dssp_emit(d, S70_SWAP);           /* lo on top */
    emit_call(d, comma_cfa);          /* emit lo */
    emit_call(d, comma_cfa);          /* emit hi */
    dssp_emit(d, S70_RET);
    emit_jump_to = prim_cfa(d, "(ejt)");

    /* again (immediate): compile JUMP back to begin's loop address */
    def_prim(d, "again", 1);
    emit_call(d, emit_jump_to);
    dssp_emit(d, S70_RET);

    /* while (immediate): emit JZERO with hole; DS: loop_addr -> loop_addr hole */
    def_prim(d, "while", 1);
    /* DS before: loop_lo loop_hi; after: loop_lo loop_hi hole_lo hole_hi */
    emit_push(d, S70_JZERO);
    emit_call(d, comma_cfa);
    dssp_emit(d, S70_HC_HERE_R);      /* loop_lo loop_hi hole_lo hole_hi */
    emit_push(d, 0);
    emit_call(d, comma_cfa);          /* lo placeholder */
    emit_push(d, 0);
    emit_call(d, comma_cfa);          /* hi placeholder */
    dssp_emit(d, S70_RET);

    /* repeat (immediate): emit JUMP back, patch while's hole with HERE */
    def_prim(d, "repeat", 1);
    /* DS: loop_addr hole */
    dssp_emit(d, S70_SWAP);           /* hole loop_addr */
    emit_call(d, emit_jump_to);       /* emits JUMP loop_addr; DS=[hole] */
    /* patch hole with HERE */
    dssp_emit(d, S70_HC_HERE_R);
    emit_push(d, 243);
    dssp_emit(d, S70_MUL);
    dssp_emit(d, S70_ADD);            /* hole here */
    dssp_emit(d, S70_HC_IMMPATCH);
    dssp_emit(d, S70_RET);

    /* until (immediate): emit JZERO back to begin's address */
    def_prim(d, "until", 1);
    /* DS: loop_lo loop_hi (loop_hi on top from BEGIN).
       Need to emit JZERO lo hi in bytecode.
       SWAP so lo is on top, then comma emits lo then hi. */
    emit_push(d, S70_JZERO);
    emit_call(d, comma_cfa);          /* emit JZERO opcode */
    dssp_emit(d, S70_SWAP);           /* loop_lo on top */
    emit_call(d, comma_cfa);          /* emit lo */
    emit_call(d, comma_cfa);          /* emit hi */
    dssp_emit(d, S70_RET);

    def_prim(d, "+until", 1);
    emit_push(d, S70_JPOS);
    emit_call(d, comma_cfa);
    dssp_emit(d, S70_SWAP);
    emit_call(d, comma_cfa);
    emit_call(d, comma_cfa);
    dssp_emit(d, S70_RET);

    def_prim(d, "-until", 1);
    emit_push(d, S70_JNEG);
    emit_call(d, comma_cfa);
    dssp_emit(d, S70_SWAP);
    emit_call(d, comma_cfa);
    emit_call(d, comma_cfa);
    dssp_emit(d, S70_RET);

    /* immediate: stub — marking words immediate requires a dedicated host call not yet implemented */
    def_prim(d, "immediate", 1);
    dssp_emit(d, S70_HC_EXECUTE);
    dssp_emit(d, S70_RET);

    /* ; (semicolon, immediate): emit RET, switch to interpret mode */
    def_prim(d, ";", 1);
    emit_push(d, S70_RET);
    emit_call(d, comma_cfa);        /* compile a RET at HERE */
    emit_push(d, 0);
    dssp_emit(d, S70_HC_STATE_W);   /* STATE = 0 */
    dssp_emit(d, S70_RET);
}

static void build_outer_interpreter(dssp_t *d)
{
    int cr_cfa  = prim_cfa(d, "cr");

    d->outer_addr = d->here;
    int loop_top  = d->here;

    /* WORD: push length (0 = end of input) */
    dssp_emit(d, S70_HC_WORD);
    dssp_emit(d, S70_DUP);
    int jz_done_hole = d->here + 1;
    emit_jmp(d, S70_JZERO, 0);         /* -> interp_done (patch) */
    dssp_emit(d, S70_POP);             /* drop length */

    /* FIND: pushes lo hi found (3 items).
       found=0 -> not found; found=1 -> found.
       On found: DS = lo hi (CFA)
       On not-found: DS = 0 0 (clean up and try number) */
    dssp_emit(d, S70_HC_FIND);
    /* JZERO pops found flag: if 0 (not found) jump, if 1 (found) fall through.
       Either way found is consumed; DS = lo hi on both paths. */
    int jz_num_hole = d->here + 1;
    emit_jmp(d, S70_JZERO, 0);         /* -> try_number */
    /* Found path: DS = lo hi */

    /* Check STATE */
    dssp_emit(d, S70_HC_STATE_R);      /* lo hi state */
    int jpos_compile_hole = d->here + 1;
    emit_jmp(d, S70_JPOS, 0);          /* -> compile_it */
    dssp_emit(d, S70_HC_EXECUTE);
    emit_jmp(d, S70_JUMP, loop_top);

    /* compile_it: */
    int compile_it = d->here;
    dssp_patch2(d, jpos_compile_hole, compile_it);
    dssp_emit(d, S70_HC_COMPILE);
    emit_jmp(d, S70_JUMP, loop_top);

    /* try_number: FIND pushed 0 0 0 (lo, hi, found=0).
       JZERO already popped found=0.  DS has lo=0 and hi=0 remaining. */
    int try_number = d->here;
    dssp_patch2(d, jz_num_hole, try_number);
    dssp_emit(d, S70_POP);   /* pop hi=0 */
    dssp_emit(d, S70_POP);   /* pop lo=0 */
    dssp_emit(d, S70_HC_NUMBER);        /* -- value ok_flag */
    dssp_emit(d, S70_DUP);
    int jz_err_hole = d->here + 1;
    emit_jmp(d, S70_JZERO, 0);         /* -> num_err (patch) */
    dssp_emit(d, S70_POP);             /* drop ok_flag; value on DS */

    dssp_emit(d, S70_HC_STATE_R);
    int jpos_cnum_hole = d->here + 1;
    emit_jmp(d, S70_JPOS, 0);          /* -> compile_num (patch) */
    emit_jmp(d, S70_JUMP, loop_top);   /* interpret: value stays on DS */

    /* compile_num: emit PUSH <value> at HERE */
    int compile_num = d->here;
    dssp_patch2(d, jpos_cnum_hole, compile_num);
    /* DS: value */
    dssp_emit(d, S70_RPUSH);           /* RS=[value] */
    emit_push(d, S70_PUSH);
    emit_call(d, prim_cfa(d, ","));    /* emit PUSH opcode at HERE */
    dssp_emit(d, S70_RPOP);
    emit_call(d, prim_cfa(d, ","));    /* emit value at HERE */
    emit_jmp(d, S70_JUMP, loop_top);

    /* num_err: print "?!" and continue */
    int num_err = d->here;
    dssp_patch2(d, jz_err_hole, num_err);
    dssp_emit(d, S70_POP);
    emit_push(d, '?');
    dssp_emit(d, S70_EMIT);
    emit_push(d, '!');
    dssp_emit(d, S70_EMIT);
    emit_call(d, cr_cfa);
    emit_jmp(d, S70_JUMP, loop_top);

    /* interp_done: */
    int interp_done = d->here;
    dssp_patch2(d, jz_done_hole, interp_done);
    dssp_emit(d, S70_POP);             /* drop the 0 from WORD */
    dssp_emit(d, S70_RET);
}

static void hc_here_r(setun70_t *vm)
{
    dssp_t *d  = g_dssp;
    int here   = d->here;
    tryte_t lo = int_to_tryte(here % 243);
    tryte_t hi = int_to_tryte(here / 243);
    setun70_ds_push(vm, &lo);
    setun70_ds_push(vm, &hi);
}

static void hc_here_w(setun70_t *vm)
{
    dssp_t *d    = g_dssp;
    tryte_t hi_t = setun70_ds_pop(vm);
    tryte_t lo_t = setun70_ds_pop(vm);
    d->here      = tryte_to_int(&lo_t) + tryte_to_int(&hi_t) * 243;
}

/* Public API */

void dssp_init(dssp_t *d)
{
    memset(d, 0, sizeof(*d));
    setun70_init(&d->vm);

    /* Place HALT sentinel at address 0 */
    tryte_t halt_op = int_to_tryte(S70_HALT);
    setun70_mem_write(&d->vm, 0, &halt_op);

    /* Wire host-call table (indexed by opcode - 27) */
    memset(hctab, 0, sizeof(hctab));
    hctab[S70_HC_WORD     - 27] = hc_word;
    hctab[S70_HC_FIND     - 27] = hc_find;
    hctab[S70_HC_NUMBER   - 27] = hc_number;
    hctab[S70_HC_DOT      - 27] = hc_dot;
    hctab[S70_HC_DOTTERN  - 27] = hc_dottern;
    hctab[S70_HC_DOTS     - 27] = hc_dots;
    hctab[S70_HC_EXECUTE  - 27] = hc_execute;
    hctab[S70_HC_COMPILE  - 27] = hc_compile;
    hctab[S70_HC_TICK     - 27] = hc_tick;
    hctab[S70_HC_STATE_R  - 27] = hc_state_r;
    hctab[S70_HC_STATE_W  - 27] = hc_state_w;
    hctab[S70_HC_HERE_R   - 27] = hc_here_r;
    hctab[S70_HC_HERE_W   - 27] = hc_here_w;
    hctab[S70_HC_IMMPATCH - 27] = hc_immpatch;
    hctab[S70_HC_COMMA    - 27] = hc_comma;
    hctab[S70_HC_ALLOT    - 27] = hc_allot;
    hctab[S70_HC_MEMW2    - 27] = hc_memw2;
    hctab[S70_HC_MEMR2    - 27] = hc_memr2;

    d->here   = DICT_START;
    d->latest = 0;
    d->state  = 0;
    d->base   = 10;

    build_primitives(d);
    build_compiler_words(d);
    build_outer_interpreter(d);
}

int dssp_eval(dssp_t *d, const char *line)
{
    g_dssp = d;

    /* Copy line into TIB */
    int len = (int) strlen(line);
    if (len >= (int) sizeof(d->tib)) len = (int) sizeof(d->tib) - 1;
    memcpy(d->tib, line, len);
    d->tib[len] = '\0';
    d->tiblen   = len;
    d->toin     = 0;

    /* Handle ":" specially — create dict header in C, then compile the body */
    int i = 0;
    while (i < len && d->tib[i] == ' ') i++;

    if (i < len && d->tib[i] == ':' &&
        (i + 1 >= len || d->tib[i + 1] == ' ')) {

        i++;
        while (i < len && d->tib[i] == ' ') i++;
        int nstart = i;
        while (i < len && d->tib[i] != ' ') i++;
        int nlen = i - nstart;

        char name[64] = {0};
        if (nlen > 63) nlen = 63;
        strncpy(name, d->tib + nstart, nlen);

        begin_word(d, name, 0);    /* writes header; CFA = d->here */
        d->state = 1;
        d->toin  = i;
    }

    /* Run the outer interpreter */
    d->vm.halted = 0;
    d->vm.error  = 0;
    d->vm.pc     = d->outer_addr;

    /* Push 2-tryte sentinel return address pointing to HALT (addr 0).
       RET pops lo then hi: push hi first, then lo. */
    tryte_t sent_hi = int_to_tryte(0);
    tryte_t sent_lo = int_to_tryte(0);
    setun70_rs_push(&d->vm, &sent_hi);
    setun70_rs_push(&d->vm, &sent_lo);

    dssp_run(d);

    g_dssp = NULL;

    if (d->vm.error) {
        d->vm.error = 0;
        return -1;
    }
    return 0;
}

void dssp_repl(dssp_t *d)
{
    char line[128];
    printf("DSSP / Setun-70 Forth  (type 'bye' to exit)\n");
    for (;;) {
        printf("| ");
        fflush(stdout);
        if (!fgets(line, sizeof(line), stdin)) break;
        int len = (int) strlen(line);
        while (len > 0 && (line[len-1] == '\n' || line[len-1] == '\r'))
            line[--len] = '\0';
        if (strcmp(line, "bye") == 0) break;
        int rc = dssp_eval(d, line);
        if (rc == 0) printf(" ok\n");
        else         printf(" error\n");
    }
}
