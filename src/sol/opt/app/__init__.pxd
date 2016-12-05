# coding=utf-8
from sol.path.paths cimport PPTC

cdef class App:
    cdef public PPTC pptc
    cdef public obj
    cdef public dict resourceCost
    cdef public unicode name
    cdef public list constraints
    cdef public objTC
    cdef public predicate