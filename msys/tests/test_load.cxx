#include "io.hxx"
#include <iostream>

using namespace desres::msys;

int main(int argc, char *argv[]) {
    for (int i=1; i<argc; i++) {
        FileFormat fmt;
        double t=-now();
        SystemPtr m = Load(argv[i], false, &fmt);
        t+=now();
        printf("%s %.3fms\n", argv[i], t*1000);
        //std::cout << "Guessed file format " << FileFormatAsString(fmt) << std::endl;
        if (!m) { 
            MSYS_FAIL("Unable to guess filetype of " << argv[i]);
        }
    }
    return 0;
}

