#include <Python.h>
#include <stdlib.h>

/* Comparison function for qsort */
static int compare_ints(const void* a, const void* b) {
    long val_a = *(const long*)a;
    long val_b = *(const long*)b;
    
    if (val_a < val_b) return -1;
    if (val_a > val_b) return 1;
    return 0;
}

/* Sort an array of integers */
static PyObject* sort_array(PyObject* self, PyObject* args) {
    PyObject* arr_obj;
    
    if (!PyArg_ParseTuple(args, "O", &arr_obj)) {
        return NULL;
    }
    
    /* Validate input type */
    if (!PyList_Check(arr_obj)) {
        PyErr_SetString(PyExc_TypeError, "Argument must be a list");
        return NULL;
    }
    
    Py_ssize_t size = PyList_Size(arr_obj);
    
    if (size == 0) {
        return PyList_New(0);
    }
    
    /* Allocate array for sorting */
    long* arr = (long*)malloc(size * sizeof(long));
    if (!arr) {
        return PyErr_NoMemory();
    }
    
    /* Convert Python list to C array */
    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject* item = PyList_GetItem(arr_obj, i);
        if (!PyLong_Check(item)) {
            free(arr);
            PyErr_SetString(PyExc_TypeError, "All elements must be integers");
            return NULL;
        }
        
        arr[i] = PyLong_AsLong(item);
        if (PyErr_Occurred()) {
            free(arr);
            return NULL;
        }
    }
    
    /* Sort the array */
    qsort(arr, size, sizeof(long), compare_ints);
    
    /* Create result list */
    PyObject* result = PyList_New(size);
    if (!result) {
        free(arr);
        return NULL;
    }
    
    /* Convert back to Python list */
    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject* item = PyLong_FromLong(arr[i]);
        if (!item) {
            free(arr);
            Py_DECREF(result);
            return NULL;
        }
        PyList_SET_ITEM(result, i, item);
    }
    
    free(arr);
    return result;
}

/* Filter array elements >= threshold */
static PyObject* filter_array(PyObject* self, PyObject* args) {
    PyObject* arr_obj;
    long threshold;
    
    if (!PyArg_ParseTuple(args, "Ol", &arr_obj, &threshold)) {
        return NULL;
    }
    
    /* Validate input type */
    if (!PyList_Check(arr_obj)) {
        PyErr_SetString(PyExc_TypeError, "First argument must be a list");
        return NULL;
    }
    
    Py_ssize_t size = PyList_Size(arr_obj);
    
    /* First pass: count elements that meet the threshold */
    Py_ssize_t count = 0;
    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject* item = PyList_GetItem(arr_obj, i);
        if (!PyLong_Check(item)) {
            PyErr_SetString(PyExc_TypeError, "All elements must be integers");
            return NULL;
        }
        
        long value = PyLong_AsLong(item);
        if (PyErr_Occurred()) {
            return NULL;
        }
        
        if (value >= threshold) {
            count++;
        }
    }
    
    /* Create result list */
    PyObject* result = PyList_New(count);
    if (!result) {
        return NULL;
    }
    
    /* Second pass: fill the result list */
    Py_ssize_t result_index = 0;
    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject* item = PyList_GetItem(arr_obj, i);
        long value = PyLong_AsLong(item);
        
        if (value >= threshold) {
            PyObject* new_item = PyLong_FromLong(value);
            if (!new_item) {
                Py_DECREF(result);
                return NULL;
            }
            PyList_SET_ITEM(result, result_index, new_item);
            result_index++;
        }
    }
    
    return result;
}

/* Method definitions */
static PyMethodDef MemoryMethods[] = {
    {"sort_array", sort_array, METH_VARARGS, 
     "Sort an array of integers"},
    {"filter_array", filter_array, METH_VARARGS, 
     "Filter array elements >= threshold"},
    {NULL, NULL, 0, NULL}
};

/* Module definition */
static struct PyModuleDef memorymodule = {
    PyModuleDef_HEAD_INIT,
    "memory",
    "C implementation of memory operation functions",
    -1,
    MemoryMethods
};

/* Module initialization */
PyMODINIT_FUNC PyInit_memory(void) {
    return PyModule_Create(&memorymodule);
}