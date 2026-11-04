/* Compatibility shim for building the msys python bindings against numpy >= 2.
 *
 * Include this immediately after <numpy/ndarrayobject.h> / <numpy/arrayobject.h>.
 *
 * numpy 2 removed the pre-1.7 flag aliases (NPY_FORCECAST, ...) and the
 * macro forms of PyArray_DIM/DATA/TYPE/NDIM that accepted a plain PyObject*.
 * msys passes PyObject* everywhere, so provide overloads that cast.
 */
#ifndef DESRES_MSYS_NUMPY_COMPAT_HXX
#define DESRES_MSYS_NUMPY_COMPAT_HXX

#if defined(NPY_ABI_VERSION) && NPY_ABI_VERSION >= 0x02000000

#ifndef NPY_FORCECAST
#define NPY_FORCECAST NPY_ARRAY_FORCECAST
#endif
#ifndef NPY_C_CONTIGUOUS
#define NPY_C_CONTIGUOUS NPY_ARRAY_C_CONTIGUOUS
#endif
#ifndef NPY_ALIGNED
#define NPY_ALIGNED NPY_ARRAY_ALIGNED
#endif
#ifndef NPY_INOUT_ARRAY
#define NPY_INOUT_ARRAY NPY_ARRAY_INOUT_ARRAY
#endif

static inline int PyArray_NDIM(const PyObject* o) {
    return PyArray_NDIM(reinterpret_cast<const PyArrayObject*>(o));
}
static inline void* PyArray_DATA(const PyObject* o) {
    return PyArray_DATA(reinterpret_cast<const PyArrayObject*>(o));
}
static inline npy_intp PyArray_DIM(const PyObject* o, int i) {
    return PyArray_DIM(reinterpret_cast<const PyArrayObject*>(o), i);
}
static inline int PyArray_TYPE(const PyObject* o) {
    return PyArray_TYPE(reinterpret_cast<const PyArrayObject*>(o));
}

#endif /* numpy >= 2 */
#endif
