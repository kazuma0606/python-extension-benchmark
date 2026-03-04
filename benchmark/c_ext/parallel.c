#include <Python.h>
#include <stdlib.h>

#ifdef WINDOWS_THREADS
#include <windows.h>
#include <process.h>
#else
#include <pthread.h>
#endif

/* Structure to pass data to thread function */
typedef struct {
    double* data;
    size_t start;
    size_t end;
    double result;
} ThreadData;

#ifdef WINDOWS_THREADS
/* Windows thread function */
static unsigned __stdcall compute_chunk_windows(void* arg) {
    ThreadData* thread_data = (ThreadData*)arg;
    double sum = 0.0;
    
    for (size_t i = thread_data->start; i < thread_data->end; i++) {
        sum += thread_data->data[i];
    }
    
    thread_data->result = sum;
    return 0;
}
#else
/* POSIX thread function */
static void* compute_chunk(void* arg) {
    ThreadData* thread_data = (ThreadData*)arg;
    double sum = 0.0;
    
    for (size_t i = thread_data->start; i < thread_data->end; i++) {
        sum += thread_data->data[i];
    }
    
    thread_data->result = sum;
    return NULL;
}
#endif

/* Perform parallel computation (sum) using multiple threads */
static PyObject* parallel_compute(PyObject* self, PyObject* args) {
    PyObject* data_obj;
    int num_threads;
    
    if (!PyArg_ParseTuple(args, "Oi", &data_obj, &num_threads)) {
        return NULL;
    }
    
    /* Validate input types */
    if (!PyList_Check(data_obj)) {
        PyErr_SetString(PyExc_TypeError, "First argument must be a list");
        return NULL;
    }
    
    if (num_threads <= 0) {
        PyErr_SetString(PyExc_ValueError, "num_threads must be positive");
        return NULL;
    }
    
    Py_ssize_t data_size = PyList_Size(data_obj);
    
    if (data_size == 0) {
        return PyFloat_FromDouble(0.0);
    }
    
    /* For single thread, compute directly */
    if (num_threads == 1) {
        double sum = 0.0;
        for (Py_ssize_t i = 0; i < data_size; i++) {
            PyObject* item = PyList_GetItem(data_obj, i);
            double value = PyFloat_AsDouble(item);
            if (PyErr_Occurred()) {
                return NULL;
            }
            sum += value;
        }
        return PyFloat_FromDouble(sum);
    }
    
    /* Convert Python list to C array */
    double* data = (double*)malloc(data_size * sizeof(double));
    if (!data) {
        return PyErr_NoMemory();
    }
    
    for (Py_ssize_t i = 0; i < data_size; i++) {
        PyObject* item = PyList_GetItem(data_obj, i);
        data[i] = PyFloat_AsDouble(item);
        if (PyErr_Occurred()) {
            free(data);
            return NULL;
        }
    }
    
    /* Limit threads to data size */
    if (num_threads > data_size) {
        num_threads = data_size;
    }
    
    /* Allocate thread data */
    ThreadData* thread_data = (ThreadData*)malloc(num_threads * sizeof(ThreadData));
    if (!thread_data) {
        free(data);
        return PyErr_NoMemory();
    }
    
#ifdef WINDOWS_THREADS
    HANDLE* threads = (HANDLE*)malloc(num_threads * sizeof(HANDLE));
    if (!threads) {
        free(data);
        free(thread_data);
        return PyErr_NoMemory();
    }
#else
    pthread_t* threads = (pthread_t*)malloc(num_threads * sizeof(pthread_t));
    if (!threads) {
        free(data);
        free(thread_data);
        return PyErr_NoMemory();
    }
#endif
    
    /* Calculate chunk sizes */
    size_t chunk_size = data_size / num_threads;
    size_t remainder = data_size % num_threads;
    
    /* Create and start threads */
    size_t start_idx = 0;
    for (int i = 0; i < num_threads; i++) {
        thread_data[i].data = data;
        thread_data[i].start = start_idx;
        
        /* Distribute remainder across first threads */
        size_t current_chunk_size = chunk_size + (i < remainder ? 1 : 0);
        thread_data[i].end = start_idx + current_chunk_size;
        thread_data[i].result = 0.0;
        
        if (start_idx < data_size) {
#ifdef WINDOWS_THREADS
            threads[i] = (HANDLE)_beginthreadex(NULL, 0, compute_chunk_windows, &thread_data[i], 0, NULL);
            if (threads[i] == 0) {
                /* Clean up and return error */
                for (int j = 0; j < i; j++) {
                    WaitForSingleObject(threads[j], INFINITE);
                    CloseHandle(threads[j]);
                }
                free(data);
                free(thread_data);
                free(threads);
                PyErr_SetString(PyExc_RuntimeError, "Failed to create thread");
                return NULL;
            }
#else
            int result = pthread_create(&threads[i], NULL, compute_chunk, &thread_data[i]);
            if (result != 0) {
                /* Clean up and return error */
                for (int j = 0; j < i; j++) {
                    pthread_join(threads[j], NULL);
                }
                free(data);
                free(thread_data);
                free(threads);
                PyErr_SetString(PyExc_RuntimeError, "Failed to create thread");
                return NULL;
            }
#endif
        }
        
        start_idx = thread_data[i].end;
    }
    
    /* Wait for all threads to complete and sum results */
    double total_sum = 0.0;
    for (int i = 0; i < num_threads; i++) {
        if (thread_data[i].start < data_size) {
#ifdef WINDOWS_THREADS
            WaitForSingleObject(threads[i], INFINITE);
            CloseHandle(threads[i]);
#else
            pthread_join(threads[i], NULL);
#endif
            total_sum += thread_data[i].result;
        }
    }
    
    /* Clean up */
    free(data);
    free(thread_data);
    free(threads);
    
    return PyFloat_FromDouble(total_sum);
}

/* Method definitions */
static PyMethodDef ParallelMethods[] = {
    {"parallel_compute", parallel_compute, METH_VARARGS, 
     "Perform parallel computation (sum) using multiple threads"},
    {NULL, NULL, 0, NULL}
};

/* Module definition */
static struct PyModuleDef parallelmodule = {
    PyModuleDef_HEAD_INIT,
    "parallel",
    "C implementation of parallel computation functions",
    -1,
    ParallelMethods
};

/* Module initialization */
PyMODINIT_FUNC PyInit_parallel(void) {
    return PyModule_Create(&parallelmodule);
}