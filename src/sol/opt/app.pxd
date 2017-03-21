# coding=utf-8
from sol.path.paths cimport PPTC

cdef class App:
    cdef public PPTC pptc
    cdef public obj
    cdef public dict resource_cost
    cdef public unicode name
    cdef public list constraints
    cdef public obj_tc
    cdef public predicate

    cpdef double volume(self)
