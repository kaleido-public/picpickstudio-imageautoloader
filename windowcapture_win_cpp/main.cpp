#include "capture.hpp"
#include <pybind11/stl.h>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

struct py_CaptureWindowOutput
{
    Size size;
    py::array_t<byte> frame;

    py_CaptureWindowOutput::py_CaptureWindowOutput(CaptureWindowOutput const &other)
        : size(other.size),
          frame(other.frame.size(), other.frame.data())
    {
    }
};

py_CaptureWindowOutput py_captureWindowBitBlt(uint64_t window)
{
    return py_CaptureWindowOutput(captureWindowBitBlt(window));
}

py_CaptureWindowOutput py_captureWindowWinRT(uint64_t window)
{
    return py_CaptureWindowOutput(captureWindowWinRT(window));
}

PYBIND11_MODULE(windowcapture_win_py, m)
{
    m.def("captureWindowBitBlt", &py_captureWindowBitBlt, "Capture a Window");
    m.def("captureWindowWinRT", &py_captureWindowWinRT, "Capture a Window");

    // py::class_<CaptureWindowOutput>(m, "CaptureWindowOutput", py::buffer_protocol())
    //     .def_buffer([](CaptureWindowOutput &m) -> py::buffer_info {
    //         return py::buffer_info(
    //             m.frame.data(),
    //             m.frame.size(),
    //             true
    //         );
    //     });

    py::class_<Size>(m, "Size")
        .def_readwrite("width", &Size::width)
        .def_readwrite("height", &Size::height);

    py::class_<py_CaptureWindowOutput>(m, "CaptureWindowOutput")
        .def_readwrite("size", &py_CaptureWindowOutput::size)
        .def_readwrite("frame", &py_CaptureWindowOutput::frame);
}
