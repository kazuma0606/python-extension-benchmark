#include <Python.h>
#include <stdlib.h>
#include <math.h>

/* Find all prime numbers up to n using Sieve of Eratosthenes */
static PyObject* find_primes(PyObject* self, PyObject* args) {
    int n;
    if (!PyArg_ParseTuple(args, "i", &n)) {
        return NULL;
    }
    
    if (n < 2) {
        return PyList_New(0);
    }
    
    /* Allocate sieve array */
    char* is_prime = (char*)calloc(n + 1, sizeof(char));
    if (!is_prime) {
        return PyErr_NoMemory();
    }
    
    /* Initialize sieve: 1 means potentially prime */
    for (int i = 2; i <= n; i++) {
        is_prime[i] = 1;
    }
    
    /* Sieve of Eratosthenes */
    int sqrt_n = (int)sqrt(n);
    for (int i = 2; i <= sqrt_n; i++) {
        if (is_prime[i]) {
            /* Mark all multiples of i as not prime */
            for (int j = i * i; j <= n; j += i) {
                is_prime[j] = 0;
            }
        }
    }
    
    /* Count primes first to allocate list */
    int prime_count = 0;
    for (int i = 2; i <= n; i++) {
        if (is_prime[i]) {
            prime_count++;
        }
    }
    
    /* Create Python list */
    PyObject* result = PyList_New(prime_count);
    if (!result) {
        free(is_prime);
        return NULL;
    }
    
    /* Fill the list with primes */
    int index = 0;
    for (int i = 2; i <= n; i++) {
        if (is_prime[i]) {
            PyObject* prime = PyLong_FromLong(i);
            if (!prime) {
                free(is_prime);
                Py_DECREF(result);
                return NULL;
            }
            PyList_SET_ITEM(result, index, prime);
            index++;
        }
    }
    
    free(is_prime);
    return result;
}

/* Multiply two matrices */
static PyObject* matrix_multiply(PyObject* self, PyObject* args) {
    PyObject* a_obj;
    PyObject* b_obj;
    
    if (!PyArg_ParseTuple(args, "OO", &a_obj, &b_obj)) {
        return NULL;
    }
    
    /* Validate input types */
    if (!PyList_Check(a_obj) || !PyList_Check(b_obj)) {
        PyErr_SetString(PyExc_TypeError, "Arguments must be lists");
        return NULL;
    }
    
    Py_ssize_t m = PyList_Size(a_obj);
    Py_ssize_t n_b = PyList_Size(b_obj);
    
    if (m == 0 || n_b == 0) {
        /* Return empty matrix */
        PyObject* result = PyList_New(1);
        PyList_SET_ITEM(result, 0, PyList_New(0));
        return result;
    }
    
    /* Get first row to determine dimensions */
    PyObject* first_row_a = PyList_GetItem(a_obj, 0);
    PyObject* first_row_b = PyList_GetItem(b_obj, 0);
    
    if (!PyList_Check(first_row_a) || !PyList_Check(first_row_b)) {
        PyErr_SetString(PyExc_TypeError, "Matrix rows must be lists");
        return NULL;
    }
    
    Py_ssize_t n = PyList_Size(first_row_a);
    Py_ssize_t p = PyList_Size(first_row_b);
    
    /* Verify dimensions are compatible */
    if (n_b != n) {
        PyErr_Format(PyExc_ValueError, 
                    "Incompatible matrix dimensions: %zdx%zd and %zdx%zd", 
                    m, n, n_b, p);
        return NULL;
    }
    
    /* Create result matrix */
    PyObject* result = PyList_New(m);
    if (!result) {
        return NULL;
    }
    
    /* Initialize result matrix with zeros */
    for (Py_ssize_t i = 0; i < m; i++) {
        PyObject* row = PyList_New(p);
        if (!row) {
            Py_DECREF(result);
            return NULL;
        }
        for (Py_ssize_t j = 0; j < p; j++) {
            PyList_SET_ITEM(row, j, PyFloat_FromDouble(0.0));
        }
        PyList_SET_ITEM(result, i, row);
    }
    
    /* Perform matrix multiplication */
    for (Py_ssize_t i = 0; i < m; i++) {
        PyObject* row_a = PyList_GetItem(a_obj, i);
        if (!PyList_Check(row_a) || PyList_Size(row_a) != n) {
            PyErr_SetString(PyExc_ValueError, "Inconsistent matrix dimensions");
            Py_DECREF(result);
            return NULL;
        }
        
        PyObject* result_row = PyList_GetItem(result, i);
        
        for (Py_ssize_t j = 0; j < p; j++) {
            double sum = 0.0;
            
            for (Py_ssize_t k = 0; k < n; k++) {
                PyObject* row_b = PyList_GetItem(b_obj, k);
                if (!PyList_Check(row_b) || PyList_Size(row_b) != p) {
                    PyErr_SetString(PyExc_ValueError, "Inconsistent matrix dimensions");
                    Py_DECREF(result);
                    return NULL;
                }
                
                PyObject* a_val = PyList_GetItem(row_a, k);
                PyObject* b_val = PyList_GetItem(row_b, j);
                
                double a_double = PyFloat_AsDouble(a_val);
                double b_double = PyFloat_AsDouble(b_val);
                
                if (PyErr_Occurred()) {
                    Py_DECREF(result);
                    return NULL;
                }
                
                sum += a_double * b_double;
            }
            
            PyObject* sum_obj = PyFloat_FromDouble(sum);
            if (!sum_obj) {
                Py_DECREF(result);
                return NULL;
            }
            
            /* Replace the zero we initialized with */
            Py_DECREF(PyList_GetItem(result_row, j));
            PyList_SET_ITEM(result_row, j, sum_obj);
        }
    }
    
    return result;
}

/* Method definitions */
static PyMethodDef NumericMethods[] = {
    {"find_primes", find_primes, METH_VARARGS, 
     "Find all prime numbers up to n using Sieve of Eratosthenes"},
    {"matrix_multiply", matrix_multiply, METH_VARARGS, 
     "Multiply two matrices"},
    {NULL, NULL, 0, NULL}
};

/* Module definition */
static struct PyModuleDef numericmodule = {
    PyModuleDef_HEAD_INIT,
    "numeric",
    "C implementation of numeric computation functions",
    -1,
    NumericMethods
};

/* Module initialization */
PyMODINIT_FUNC PyInit_numeric(void) {
    return PyModule_Create(&numericmodule);
}