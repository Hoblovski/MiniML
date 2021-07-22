#ifndef TEST_H
#define TEST_H

#include <stdlib.h>
#include <assert.h>
#include <stdio.h>

#define STATIC_ASSERT(COND, MSG) static int static_assertion_##MSG[(COND)?1:-1]

STATIC_ASSERT(sizeof(int) == 4, bad_int_size);
STATIC_ASSERT(sizeof(void*) == 4, bad_ptr_size);

typedef int val;

val ep=0;
val sp=0;

// for pc we shall use the computer's pc

typedef void (*fn_t)(void);
#define sp_next     (*(val*) (sp+0))
#define sp_v        (*(val*) (sp+4))
#define ep_next     (*(val*) (ep+0))
#define ep_v        (*(val*) (ep+4))
#define load(a)     (*(val*) (a))
#define store(a, v) ((*(val*) (a)) = ((val) (v)))
#define call(fn)    (((fn_t) (fn))())

static inline val _new(int n) {
    val rv = (val) malloc(n);
    assert(rv != 0 && "malloc returns NULL");
    return rv;
}

static inline void _pushs(val v) {
    val t = _new(8);
    store(t, sp);
    store(t+4, v);
    sp = t;
}

static inline val _pops() {
    val r = load(sp+4);
    sp = load(sp);
    return r;
}

static inline void _pushe(val v) {
    val t = _new(8);
    store(t, ep);
    store(t+4, v);
    ep = t;
}

static inline val _pope() {
    val r = load(ep+4);
    ep = load(ep);
    return r;
}

static inline void _pushe1(val *ep, val v) {
    val t = _new(8);
    store(t, *ep);
    store(t+4, v);
    *ep = t;
}

#define Iclosure(lam) do {                     \
    val t = _new(3*4);                         \
    store(t, lam);                             \
    store(t+4, 0);                             \
    store(t+8, ep);                            \
    _pushs(t);                                 \
} while (0);

#define Iapply() do {                          \
    val v = _pops();                           \
    val t = _pops();                           \
    val fn = load(t);                          \
    val fns = load(t+4);                       \
    val ep1 = load(t+8);                       \
    if (fns != 0) _pushe1(&ep1, t);            \
    _pushe1(&ep1, v);                          \
    _pushs(ep);                                \
    ep = ep1;                                  \
    call(fn);                                  \
} while (0);

#define Iaccess(n) do {                        \
    val t = ep;                                \
    for (int i = 1; i < n; i++)                \
        t = load(t);                           \
    t = load(t+4);                             \
    _pushs(t);                                 \
} while (0);

#define Iconstint(n) do {                      \
    _pushs(n);                                 \
} while (0);

#define Ireturn() do {                         \
    val v = _pops();                           \
    val ep1 = _pops();                         \
    _pushs(v);                                 \
    ep = ep1;                                  \
    return;                                    \
} while (0);

#define Ibinary(op) do {                       \
    val rhs = _pops();                         \
    val lhs = _pops();                         \
    _pushs(lhs op rhs);                        \
} while (0);

#define Iclosures(...) do {                    \
    fn_t fns[] =  { __VA_ARGS__ };             \
    int len = sizeof(fns) / sizeof(fns[0]);    \
    val t = _new(3*4);                         \
    store(t, 0);                               \
    val t1 = _new(len*4);                      \
    store(t+4, t1);                            \
    for (int i = 0; i < len; i++)              \
        store(t1 + 4*i, fns[i]);               \
    store(t+8, ep);                            \
    _pushe(t);                                 \
} while (0);

#define Ifocus(n) do {                         \
    val t = _pops();                           \
    val fns = load(t+4);                       \
    val fn = load(fns + 4*(n-1));              \
    store(t, fn);                              \
    _pushs(t);                                 \
} while (0);

#define Ipop(n) do {                           \
    for (int i = 0; i < n; i++) sp = load(sp); \
} while (0);

#define Ibuiltin(fn) do {                      \
    Iclosure(builtin_ ## fn);                  \
} while (0);

#define Ihalt() do {                           \
    return;                                    \
} while (0);

#define Ilabel(lbl) lbl:

#define Ibr(lbl) do {                          \
    goto lbl ;                                 \
} while (0);

#define Ibr1(pred, lbl) do {                   \
    val t = _pops();                           \
    if (pred (t)) goto lbl;                    \
} while (0);

static inline void builtin_println(void) {
    val v = ep_v;
    printf("%d\n", v);
    _pushs(0);  // placeholder for unit
    Ireturn();
}


#endif // TEST_H
