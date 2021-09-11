#include "launcher.h"
#include <Python.h>

#define PYD_NAME L"msv.cp39-win_amd64.pyd"

static const char SCRIPT[] =
"import sys\n"
"import multiprocessing\n"
"from msv import main_entry\n"
"\n"
"if __name__ == \"__main__\":\n"
"    multiprocessing.freeze_support()\n"
"    sys.exit(main_entry())\n"
;
static const wchar_t* EXTRA_ARGS[] = {
    L"-t", L"Aqua"
};
#define EXTRA_ARGS_LEN (sizeof(EXTRA_ARGS) / sizeof(EXTRA_ARGS[0]))


void init_python(int argc, wchar_t* argv[]) {
    PyConfig config;
    PyConfig_InitPythonConfig(&config);
    config.user_site_directory = 0;
    config.parse_argv = 0;

    /* Set the program name. Implicitly preinitialize Python. */
    PyStatus status = PyConfig_SetString(&config, &config.program_name, argv[0]);
    if (PyStatus_Exception(status)) {
        goto fail;
    }

    status = PyConfig_SetArgv(&config, argc, argv);
    if (PyStatus_Exception(status)) {
        goto fail;
    }

    status = Py_InitializeFromConfig(&config);
    if (PyStatus_Exception(status)) {
        goto fail;
    }
    PyConfig_Clear(&config);
    return;

fail:
    PyConfig_Clear(&config);
    Py_ExitStatusException(status);
}


int wmain(int argc, wchar_t* argv[]) {
    if (GetFileAttributes(PYD_NAME) == INVALID_FILE_ATTRIBUTES) {
        MessageBox(0, L"DLL missing", L"Error", MB_ICONERROR);
        return -1;
    }
    
    if (argc == 5 && wcscmp(argv[argc - 1], L"--multiprocessing-fork") == 0) {  // child process
        // cmd example: E:\workspace\msv_python\aqua.exe" "-I" "-c" "from multiprocessing.spawn import spawn_main; spawn_main(parent_pid=31308, pipe_handle=2016)" "--multiprocessing-fork"'
        return Py_Main(argc, argv);
    } else {  // main process
        int new_argc = argc + EXTRA_ARGS_LEN;
        auto new_argv = static_cast<wchar_t**>(malloc(sizeof(wchar_t*) * new_argc));
        if (new_argv == nullptr) {
            return -1;
        }
        for (int i = 0; i < argc; i++) {
            new_argv[i] = argv[i];
        }
        for (int i = 0; i < EXTRA_ARGS_LEN; i++) {
            new_argv[argc+i] = const_cast<wchar_t*>(EXTRA_ARGS[i]);
        }
        
        init_python(new_argc, new_argv);
        PyRun_SimpleString(SCRIPT);
        if (Py_FinalizeEx() < 0) {
            exit(120);
        }
    }

    return 0;
}
